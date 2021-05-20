"""
Custom Permissions for edx-sysadmin API Views
"""

from hashlib import sha256
import hmac
import logging

from django.conf import settings
from django.utils.encoding import force_bytes
from rest_framework import permissions, status
from rest_framework.exceptions import APIException
from rest_framework.response import Response


logger = logging.getLogger(__name__)


class GithubWebhookPermissionException(APIException):
    """
    API Exception for github webhook request
    """

    status_code = status.HTTP_403_FORBIDDEN
    default_code = "not_authenticated"


class GithubWebhookPermission(permissions.BasePermission):
    """
    Validates Github webhook request permissions
    :returns boolean: True if permission is valid else False
    """

    def has_permission(self, request, view):
        def _validate_github_webhook_signature(request):
            """
            Validate Github webhook request signature
            :returns boolean: True if HMAC matches else False
            :returns str: Error messages
            """
            if not hasattr(settings, "SYSADMIN_GITHUB_WEBHOOK_KEY"):
                return (
                    False,
                    "SYSADMIN_GITHUB_WEBHOOK_KEY is not configured in settings",
                )

            header_signature = request.headers.get("X-Hub-Signature-256")
            if header_signature is None:
                return False, "X-Hub-Signature-256 not found in request headers"

            sha_name, signature = header_signature.split("=")
            if sha_name != "sha256":
                return False, "Signature is not using sha256"

            mac = hmac.new(
                force_bytes(settings.SYSADMIN_GITHUB_WEBHOOK_KEY),
                msg=force_bytes(request.body),
                digestmod=sha256,
            )
            if not hmac.compare_digest(
                force_bytes(mac.hexdigest()), force_bytes(signature)
            ):
                return False, "Signatures didn't match"

            return True, ""

        is_valid, err_msg = _validate_github_webhook_signature(request)

        if not is_valid:
            logger.exception(f"{self.__class__.__name__}:: {err_msg}")
            raise GithubWebhookPermissionException(detail=err_msg)

        return is_valid
