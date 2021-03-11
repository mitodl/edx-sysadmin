"""
edx_sysadmin Django application initialization.
"""
from django.apps import AppConfig

from edx_django_utils.plugins import PluginURLs

from openedx.core.djangoapps.plugins.constants import ProjectType


class EdxSysAdminConfig(AppConfig):
    """
    Configuration for the edx_sysadmin Django application.
    """

    name = "edx_sysadmin"
    verbose_name = "Open edX SysAdmin"

    plugin_app = {
        "url_config": {
            "lms.djangoapp": {
                "namespace": "sysadmin",
                "regex": "^sysadmin/",
            }
        },
    }
