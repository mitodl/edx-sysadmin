"""
Tests for Permissions
"""

from unittest.mock import patch
from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.response import Response


class GithubWebhookPermissionTestCase(TestCase):
    """
    Test Case for GithubWebhookPermission permission
    """

    SYSADMIN_GITHUB_WEBHOOK_KEY = "nuiVypAArY7lFDgMdyC5kwutDGQdDc6rXljuIcI5iBttpPebui"
    VALID_SIGNATURE = "313aa3f017c815f6677f66d9acb87cee1adc0a3ef2998b7add789aab0632a0e6"

    def setUp(self):
        super().setUp()
        self.client = APIClient()

    def test_GithubWebhookPermission_without_key(self):
        """Test GithubWebhookPermission without signature key"""

        response = self.client.post(reverse("sysadmin:api:git-reload"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @override_settings(SYSADMIN_GITHUB_WEBHOOK_KEY=SYSADMIN_GITHUB_WEBHOOK_KEY)
    @patch(
        "edx_sysadmin.api.views.GitReloadAPIView.post",
        return_value=Response({}, status=status.HTTP_200_OK),
    )
    def test_GithubWebhookPermission_with_invalid_key(self, mocked_post_method):
        """Test GithubWebhookPermission with invalid signature key"""

        response = self.client.post(
            reverse("sysadmin:api:git-reload"),
            {"data": "demo data"},
            format="json",
            **{
                "HTTP_X_Hub_Signature_256": "sha256=aa3c28d9ec0a5d3c57b5cdf69c90146250ed045f706ad919bc0fa09da197554d"
            },
        )

        mocked_post_method.assert_not_called()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @override_settings(SYSADMIN_GITHUB_WEBHOOK_KEY=SYSADMIN_GITHUB_WEBHOOK_KEY)
    @patch(
        "edx_sysadmin.api.views.GitReloadAPIView.post",
        return_value=Response({}, status=status.HTTP_200_OK),
    )
    def test_GithubWebhookPermission_with_valid_key(self, mocked_post_method):
        """Test GithubWebhookPermission with valid signature key"""

        response = self.client.post(
            reverse("sysadmin:api:git-reload"),
            {"data": "demo data"},
            format="json",
            **{
                "HTTP_X_Hub_Signature_256": f"sha256={self.VALID_SIGNATURE}",
            },
        )

        mocked_post_method.assert_called()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
