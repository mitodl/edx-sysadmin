"""
Provide extra utilities for templates
"""

from django import template
from django.utils.timezone import utc as UTC
from django.conf import settings
from common.djangoapps.util.date_utils import get_time_display, DEFAULT_DATE_TIME_FORMAT

register = template.Library()


@register.simple_tag
def change_time_display(cil_created):
    """change time display to defualt settings format"""
    return get_time_display(
        cil_created.replace(tzinfo=UTC),
        DEFAULT_DATE_TIME_FORMAT,
        coerce_tz=settings.TIME_ZONE,
    )
