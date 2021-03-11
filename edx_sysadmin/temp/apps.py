"""
App configuration for Open edX SysAdmin Plugin
"""

from django.apps import AppConfig

from edx_django_utils.plugins import PluginURLs

from openedx.core.djangoapps.plugins.constants import ProjectType


class EdxSysAdminConfig(AppConfig):
    name = "edx_sysadmin"
    verbose_name = "Open edX SysAdmin"

    plugin_app = {
        # Configuration setting for Plugin URLs for this app.
        PluginURLs.CONFIG: {
            # Configure the Plugin URLs for each project type, as needed.
            ProjectType.LMS: {
                # The namespace to provide to django's urls.include.
                PluginURLs.NAMESPACE: "sysadmin",
                # The application namespace to provide to django's urls.include.
                # Optional; Defaults to None.
                PluginURLs.APP_NAME: "sysadmin",
                # # The regex to provide to django's urls.url.
                # # Optional; Defaults to r''.
                PluginURLs.REGEX: r"^sysadmin/",
                # # The python path (relative to this app) to the URLs module to be plugged into the project.
                # # Optional; Defaults to u'urls'.
                # PluginURLs.RELATIVE_PATH: u'api.urls',
            }
        },
    }
