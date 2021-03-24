# pylint: disable=import-error
"""
Views for the Open edX SysAdmin Plugin
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.utils.html import escape
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import condition
from django.views.generic.base import TemplateView

from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore

from edx_sysadmin.forms import UserRegistrationForm
from edx_sysadmin.utils.markup import HTML, Text
from edx_sysadmin.utils.utils import (
    create_user_account,
    get_course_by_id,
    get_registration_required_extra_fields_with_values,
    is_registration_api_functional,
)


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
                    div_end="</div>",
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
