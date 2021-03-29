"""
URLs for edx_sysadmin.
"""
from django.conf.urls import url

from edx_sysadmin.views import (
    CoursesPanel, 
    SysadminDashboardView, 
    UsersPanel, 
    GitImport, 
    GitLogs,
)

app_name = "sysadmin"


urlpatterns = [
    url("^$", SysadminDashboardView.as_view(), name="sysadmin"),
    url(r"^courses/?$", CoursesPanel.as_view(), name="courses"),
    url(r"^gitimport/$", GitImport.as_view(), name='gitimport'),
    url(r'^gitlogs/?$', GitLogs.as_view(), name="gitlogs"),
    url(r'^gitlogs/(?P<course_id>.+)$', GitLogs.as_view(),
        name="gitlogs_detail"),
    url(r"^users/$", UsersPanel.as_view(), name="users"),
]
