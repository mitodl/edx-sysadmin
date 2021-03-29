# pylint: disable=import-error
"""
Views for the Open edX SysAdmin Plugin
"""
import json
import logging
import os
import subprocess
import warnings

import mongoengine
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import Http404
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.utils.html import escape
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import condition
from django.views.generic.base import TemplateView
from path import Path as path
from io import StringIO

from common.djangoapps.student.roles import CourseInstructorRole, CourseStaffRole
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore

from edx_sysadmin.git_import import GitImportError
from edx_sysadmin import git_import
from edx_sysadmin.forms import UserRegistrationForm
from edx_sysadmin.models import CourseImportLog
from edx_sysadmin.utils.markup import HTML, Text
from edx_sysadmin.utils.utils import (
    create_user_account,
    get_course_by_id,
    get_registration_required_extra_fields_with_values,
    is_registration_api_functional,
)

log = logging.getLogger(__name__)


@method_decorator(ensure_csrf_cookie, name="dispatch")
@method_decorator(staff_member_required, name="dispatch")
@method_decorator(
    cache_control(no_cache=True, no_store=True, must_revalidate=True), name="dispatch"
)
@method_decorator(condition(etag_func=None), name="dispatch")
class SysadminDashboardView(TemplateView):
    """View to show the Dashboard page of SysAdmin."""

    template_name = "edx_sysadmin/base.html"

    def __init__(self, **kwargs):
        """
        Initialize base sysadmin dashboard class with modulestore,
        modulestore_type and return msg
        """

        self.def_ms = modulestore()
        self.msg = ""
        super().__init__(**kwargs)


class CoursesPanel(SysadminDashboardView):
    """
    This manages deleting courses.
    """

    template_name = "edx_sysadmin/courses.html"

    def post(self, request):
        """Handle delete action from courses view"""

        action = request.POST.get("action", "")
        if action == "del_course":
            course_id = request.POST.get("course_id", "").strip()
            course_key = CourseKey.from_string(course_id)
            course_found = False
            try:
                course = get_course_by_id(course_key)
                course_found = True
            except Exception as err:  # pylint: disable=broad-except
                self.msg += Text(
                    _(
                        "{div_start} Error - cannot get course with ID {course_key} {error} {div_end}"
                    )
                ).format(
                    div_start=HTML("<div class='error'>"),
                    course_key=course_key,
                    error=HTML("<br/><pre>{error}</pre>").format(
                        error=escape(str(err))
                    ),
                    div_end=HTML("</div>"),
                )

            if course_found:
                # delete course that is stored with mongodb backend
                self.def_ms.delete_course(course.id, request.user.id)
                # don't delete user permission groups, though
                self.msg += Text(
                    _(
                        "{font_start} Deleted {location} = {course_id} {course_name} {font_end}"
                    )
                ).format(
                    font_start=HTML("<font class='success'>"),
                    location=course.location,
                    course_id=course.id,
                    course_name=course.display_name,
                    font_end=HTML("</font>"),
                )

        context = {"msg": self.msg}
        return render(request, self.template_name, context)


class UsersPanel(SysadminDashboardView):
    """View to show the User Panel of SysAdmin."""

    template_name = "edx_sysadmin/users.html"

    def get_context_data(self, **kwargs):
        """
        Overriding get_context_data method to add custom fields
        """
        context = super().get_context_data(**kwargs)
        initial_data = kwargs.pop("initial_data", None)
        extra_fields = get_registration_required_extra_fields_with_values()

        if not is_registration_api_functional():
            context["disclaimer"] = True

        context["user_registration_form"] = UserRegistrationForm(
            initial_data, extra_fields=extra_fields
        )
        return context

    def post(self, request, *args, **kwargs):  # pylint: disable=unused-argument
        """
        POST method for User registration
        """
        extra_fields = get_registration_required_extra_fields_with_values()
        form = UserRegistrationForm(request.POST, extra_fields=extra_fields)
        context = self.get_context_data(initial_data=request.POST, **kwargs)

        if form.is_valid():
            context.update(
                create_user_account(form.cleaned_data, request.build_absolute_uri)
            )
        else:
            context["error_message"] = _(
                "Unable to create new account due to invalid data"
            )

        return render(request, self.template_name, context)


class GitImport(SysadminDashboardView):
    """
    This provide the view to load new course from github
    """

    template_name = "edx_sysadmin/gitimport.html"

    def get_course_from_git(self, gitloc, branch):
        """This downloads and runs the checks for importing a course in git"""

        if not (
            gitloc.endswith(".git")
            or gitloc.startswith("http:")
            or gitloc.startswith("https:")
            or gitloc.startswith("git:")
        ):
            return _(
                "The git repo location should end with '.git', " "and be a valid url"
            )

        return self.import_mongo_course(gitloc, branch)

    def import_mongo_course(self, gitloc, branch):
        """
        Imports course using management command and captures logging output
        at debug level for display in template
        """

        msg = u""

        log.debug(u"Adding course using git repo %s", gitloc)

        # Grab logging output for debugging imports
        output = StringIO()
        import_log_handler = logging.StreamHandler(output)
        import_log_handler.setLevel(logging.DEBUG)

        logger_names = [
            "xmodule.modulestore.xml_importer",
            "lms.djangoapps.dashboard.git_import",
            "xmodule.modulestore.xml",
            "xmodule.seq_module",
        ]
        loggers = []

        for logger_name in logger_names:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.DEBUG)
            logger.addHandler(import_log_handler)
            loggers.append(logger)

        error_msg = ""
        try:
            git_import.add_repo(gitloc, None, branch)
        except GitImportError as ex:
            error_msg = str(ex)
        ret = output.getvalue()

        # Remove handler hijacks
        for logger in loggers:
            logger.setLevel(logging.NOTSET)
            logger.removeHandler(import_log_handler)

        if error_msg:
            msg_header = error_msg
            color = "red"
        else:
            msg_header = _("Added Course")
            color = "blue"

        msg = HTML(u"<h4 style='color:{0}'>{1}</h4>").format(color, msg_header)
        msg += HTML(u"<pre>{0}</pre>").format(escape(ret))
        return msg

    def post(self, request):
        """Handle all actions from courses view"""

        if not request.user.is_staff:
            raise Http404

        action = request.POST.get("action", "")

        if action == "add_course":
            gitloc = (
                request.POST.get("repo_location", "")
                .strip()
                .replace(" ", "")
                .replace(";", "")
            )
            branch = (
                request.POST.get("repo_branch", "")
                .strip()
                .replace(" ", "")
                .replace(";", "")
            )
            self.msg += self.get_course_from_git(gitloc, branch)

        context = {"msg": self.msg}
        return render(request, self.template_name, context)


class GitLogs(SysadminDashboardView):
    """
    This provides a view into the import of courses from git repositories.
    It is convenient for allowing course teams to see what may be wrong with
    their xml
    """

    template_name = "edx_sysadmin/gitlogs.html"

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        """Shows logs of imports that happened as a result of a git import"""

        course_id = kwargs.get("course_id")
        if course_id:
            course_id = CourseKey.from_string(course_id)

        page_size = 10

        # Set mongodb defaults even if it isn't defined in settings
        mongo_db = {
            "host": "localhost",
            "user": "",
            "password": "",
            "db": "xlog",
        }

        # Allow overrides
        if hasattr(settings, "MONGODB_LOG"):
            for config_item in [
                "host",
                "user",
                "password",
                "db",
            ]:
                mongo_db[config_item] = settings.MONGODB_LOG.get(
                    config_item, mongo_db[config_item]
                )

        mongouri = "mongodb://{user}:{password}@{host}/{db}".format(**mongo_db)

        error_msg = ""

        try:
            if mongo_db["user"] and mongo_db["password"]:
                mdb = mongoengine.connect(mongo_db["db"], host=mongouri)
            else:
                mdb = mongoengine.connect(mongo_db["db"], host=mongo_db["host"])
        except mongoengine.connection.ConnectionError:
            log.exception(
                "Unable to connect to mongodb to save log, "
                "please check MONGODB_LOG settings."
            )

        if course_id is None:
            # Require staff if not going to specific course
            if not request.user.is_staff:
                raise Http404
            cilset = CourseImportLog.objects.order_by("-created")
        else:
            # Allow only course team, instructors, and staff
            if not (
                request.user.is_staff
                or CourseInstructorRole(course_id).has_user(request.user)
                or CourseStaffRole(course_id).has_user(request.user)
            ):
                raise Http404
            log.debug("course_id=%s", course_id)
            cilset = CourseImportLog.objects.filter(course_id=course_id).order_by(
                "-created"
            )
            log.debug(u"cilset length=%s", len(cilset))

        # Paginate the query set
        paginator = Paginator(cilset, page_size)
        try:
            logs = paginator.page(request.GET.get("page"))
        except PageNotAnInteger:
            logs = paginator.page(1)
        except EmptyPage:
            # If the page is too high or low
            given_page = int(request.GET.get("page"))
            page = min(max(1, given_page), paginator.num_pages)
            logs = paginator.page(page)

        mdb.close()
        context = {
            "logs": logs,
            "course_id": course_id if course_id else None,
            "error_msg": error_msg,
            "page_size": page_size,
        }

        return render(request, self.template_name, context)
