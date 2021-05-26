"""
Tests for Permissions
"""
import ddt

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.response import Response


SYSADMIN_GITHUB_WEBHOOK_KEY = "nuiVypAArY7lFDgMdyC5kwutDGQdDc6rXljuIcI5iBttpPebui"
VALID_SIGNATURE = "313aa3f017c815f6677f66d9acb87cee1adc0a3ef2998b7add789aab0632a0e6"
INVALID_SIGNATURE = "aa3c28d9ec0a5d3c57b5cdf69c90146250ed045f706ad919bc0fa09da197554d"


@ddt.ddt
class GithubWebhookPermissionTestCase(TestCase):
    """
    Test Case for GithubWebhookPermission permission
    """

    def setUp(self):
        super().setUp()
        self.client = APIClient()

    def test_GithubWebhookPermission_without_key(self):
        """Test GithubWebhookPermission without signature key"""

        response = self.client.post(reverse("sysadmin:api:git-reload"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @override_settings(SYSADMIN_GITHUB_WEBHOOK_KEY=SYSADMIN_GITHUB_WEBHOOK_KEY)
    @ddt.data(
        (VALID_SIGNATURE, status.HTTP_400_BAD_REQUEST),
        (INVALID_SIGNATURE, status.HTTP_403_FORBIDDEN),
    )
    @ddt.unpack
    def test_GithubWebhookPermission_with_keys(self, signature, code):
        """Test GithubWebhookPermission with signature keys"""

        response = self.client.post(
            reverse("sysadmin:api:git-reload"),
            {"data": "demo data"},
            format="json",
            **{"HTTP_X_Hub_Signature_256": f"sha256={signature}"},
        )

        self.assertEqual(response.status_code, code)
