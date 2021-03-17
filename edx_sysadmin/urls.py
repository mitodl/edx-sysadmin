"""
URLs for edx_sysadmin.
"""
from django.conf.urls import url

from edx_sysadmin.views import SysadminDashboardView, Courses

app_name = "sysadmin"


urlpatterns = [
    url("^$", SysadminDashboardView.as_view(), name="sysadmin"),
    url(r"^courses/?$", Courses.as_view(), name="sysadmin_courses"),
]
