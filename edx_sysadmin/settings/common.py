"""
Common environment variables unique to the edx-sysadmin plugin.
"""


def plugin_settings(settings):
    """Settings for the edx-sysadmin plugin."""

    settings.GIT_REPO_DIR = "/edx/var/edxapp/course_repos"
    settings.GIT_IMPORT_STATIC = True
    settings.GIT_IMPORT_PYTHON_LIB = True
