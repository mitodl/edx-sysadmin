"""
Decorators for edx-sysadmin api
"""
from functools import wraps
from hashlib import sha256
import hmac
import logging

from django.conf import settings
from django.utils.encoding import force_bytes
from rest_framework import status
from rest_framework.response import Response


logger = logging.getLogger(__name__)


def authenticate_github_request():
    """
    Decorator for views that checks that the user passes the given test,
    and if not raise Http404. The test_func should be a callable
    that takes the user object and returns True if the user passes.
    """

    def validate_github_token(request):
        """
        Validates Github request
        :returns boolean: True if HMAC matches else False
        """
        if not hasattr(settings, "SYSADMIN_GITHUB_WEBHOOK_KEY"):
            logger.exception(
                "SYSADMIN_GITHUB_WEBHOOK_KEY is not configured in settings"
            )
            return False

        header_signature = request.headers.get("X-Hub-Signature-256")
        if header_signature is None:
            return False

        sha_name, signature = header_signature.split("=")
        if sha_name != "sha256":
            return False

        mac = hmac.new(
            force_bytes(settings.SYSADMIN_GITHUB_WEBHOOK_KEY),
            msg=force_bytes(request.body),
            digestmod=sha256,
        )
        if not hmac.compare_digest(
            force_bytes(mac.hexdigest()), force_bytes(signature)
        ):
            return False

        return True

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            logger.debug("Git reload API request has been received")
            if validate_github_token(request):
                return view_func(request, *args, **kwargs)
            else:
                logger.exception("Git reload API request couldn't pass authentication")
                return Response(
                    {"message": "Access Denied"}, status=status.HTTP_403_FORBIDDEN
                )

        return _wrapped_view

    return decorator
