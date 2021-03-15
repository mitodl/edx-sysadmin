"""
URLs for edx_sysadmin.
"""
from django.conf.urls import url

from edx_sysadmin.views import IndexPage

app_name = "sysadmin"


urlpatterns = [
    url(r"", IndexPage.as_view(), name="index_page"),
]
