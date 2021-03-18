"""
Views for the Open edX SysAdmin Plugin
"""

from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.html import escape
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import condition
from django.views.generic.base import TemplateView
from opaque_keys.edx.keys import CourseKey
from six import StringIO, text_type
from xmodule.modulestore.django import modulestore

from .utils.markup import HTML
from .utils.utility import get_course_by_id


class SysadminDashboardView(TemplateView):
    """View to show the Dashboard page of SysAdmin."""

    template_name = "edx_sysadmin/base.html"

    def __init__(self, **kwargs):
        """
        Initialize base sysadmin dashboard class with modulestore,
        modulestore_type and return msg
        """

        self.def_ms = modulestore()
        self.msg = u""
        super(SysadminDashboardView, self).__init__(**kwargs)

    @method_decorator(ensure_csrf_cookie)
    @method_decorator(login_required)
    @method_decorator(cache_control(no_cache=True, no_store=True, must_revalidate=True))
    @method_decorator(condition(etag_func=None))
    def dispatch(self, *args, **kwargs):
        return super(SysadminDashboardView, self).dispatch(*args, **kwargs)


class Courses(SysadminDashboardView):
    """
    This manages deleting courses.
    """

    template_name = "edx_sysadmin/courses.html"

    def get(self, request):
        """Displays forms and course information"""

        if not request.user.is_staff:
            raise Http404

        context = {}
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle delete action from courses view"""

        if not request.user.is_staff:
            raise Http404

        action = request.POST.get("action", "")
        if action == "del_course":
            course_id = request.POST.get("course_id", "").strip()
            course_key = CourseKey.from_string(course_id)
            course_found = False
            try:
                course = get_course_by_id(course_key)
                course_found = True
            except Exception as err:  # pylint: disable=broad-except
                self.msg += _(
                    HTML(
                        u'<div class="error">Error - cannot get course with ID {0}<br/><pre>{1}</pre></div>'
                    )
                ).format(course_key, escape(str(err)))

            if course_found:
                # delete course that is stored with mongodb backend
                self.def_ms.delete_course(course.id, request.user.id)
                # don't delete user permission groups, though
                self.msg += HTML(
                    u"<font class='success'>{0} {1} = {2} ({3})</font>"
                ).format(
                    _("Deleted"),
                    text_type(course.location),
                    text_type(course.id),
                    course.display_name,
                )

        context = {"msg": self.msg}
        return render(request, self.template_name, context)
