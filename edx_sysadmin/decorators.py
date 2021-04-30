"""
Decorators for edx-sysadmin
"""
from functools import wraps
from django.http import Http404


def check_access(test_func):
    """
    Decorator for views that checks that the user passes the given test,
    and if not raise Http404. The test_func should be a callable
    that takes the user object and returns True if the user passes.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if test_func(request.user):
                return view_func(request, *args, **kwargs)
            else:
                raise Http404

        return _wrapped_view

    return decorator
