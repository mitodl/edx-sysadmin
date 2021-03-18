"""
URLs for edx_sysadmin.
"""
from django.conf.urls import url

from edx_sysadmin.views import CoursesPanel, SysadminDashboardView, UsersPanel

app_name = "sysadmin"


urlpatterns = [
    url("^$", SysadminDashboardView.as_view(), name="sysadmin"),
    url(r"^courses/?$", CoursesPanel.as_view(), name="sysadmin_courses"),
    url(r"^users/$", UsersPanel.as_view(), name="sysadmin_users"),
]
