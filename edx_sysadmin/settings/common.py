"""
Common environment variables unique to the edx-sysadmin plugin.
"""


def plugin_settings(settings):
    """Settings for the edx-sysadmin plugin."""
    settings.SYSADMIN_GITHUB_WEBHOOK_KEY = None
    settings.SYSADMIN_DEFAULT_BRANCH = None
    settings.GIT_REPO_DIR = "/edx/var/edxapp/course_repos"
    settings.GIT_IMPORT_STATIC = True
    settings.GIT_IMPORT_PYTHON_LIB = True
