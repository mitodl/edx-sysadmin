"""
Views for the Open edX SysAdmin Plugin
"""

from django.views.generic.base import TemplateView


class IndexPage(TemplateView):
    """View to show the Index page of SysAdmin."""

    template_name = "edx_sysadmin/base.html"
