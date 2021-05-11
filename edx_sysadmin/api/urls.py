"""
URLs for edx_sysadmin.
"""
from django.conf.urls import url, include

from edx_sysadmin.api.views import (
    GitReloadAPIView,
)

app_name = "api"

urlpatterns = [
    url("^gitreload/$", GitReloadAPIView.as_view(), name="git-reload"),
]
