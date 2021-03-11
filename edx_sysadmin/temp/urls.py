"""
Contains URLs for the Open edX SysAdmin Plugin
"""

from django.urls import re_path
from edx_sysadmin.views import (
    IndexPage,
)


app_name = "sysadmin"


urlpatterns = [
    re_path(r"", IndexPage.as_view(), name="index_page"),
]
