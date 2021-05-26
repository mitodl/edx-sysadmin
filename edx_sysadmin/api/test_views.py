"""
Tests for Permissions
"""
import ddt
from unittest.mock import patch

from git import Repo

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.response import Response


SYSADMIN_GITHUB_WEBHOOK_KEY = "nuiVypAArY7lFDgMdyC5kwutDGQdDc6rXljuIcI5iBttpPebui"


@ddt.ddt
class GitReloadAPIViewTestCase(TestCase):
    """
    Test Case for GithubWebhookPermission permission
    """

    def setUp(self):
        super().setUp()
        self.client = APIClient()

    @override_settings(SYSADMIN_GITHUB_WEBHOOK_KEY=SYSADMIN_GITHUB_WEBHOOK_KEY)
    @patch(
        "edx_sysadmin.api.views.get_local_active_branch", return_value="ref/head/master"
    )
    @patch("edx_sysadmin.api.views.get_local_course_repo", return_value=Repo())
    @patch("edx_sysadmin.api.views.add_repo")
    @ddt.data(
        (
            "dd930da0a34996332e8c983aaeeb9e1cca45cc9b92492f47774d351de4740bb2",
            "ref/head/master",
            "push",
            "edx4edx_lite",
            "git@github.com:edx/edx4edx_lite.git",
            status.HTTP_200_OK,
        ),
        (
            "dd930da0a34996332e8c983aaeeb9e1cca45cc9b92492f47774d351de4740ddc",
            "ref/head/master",
            "push",
            "edx4edx_lite",
            "git@github.com:edx/edx4edx_lite.git",
            status.HTTP_403_FORBIDDEN,
        ),
        (
            "66228e6cbb54b81872b32325d8ee11ee9bca82605a89cf996dab1575f65d1413",
            "ref/head/dev",
            "push",
            "edx4edx_lite",
            "git@github.com:edx/edx4edx_lite.git",
            status.HTTP_400_BAD_REQUEST,
        ),
        (
            "dd930da0a34996332e8c983aaeeb9e1cca45cc9b92492f47774d351de4740bb2",
            "ref/head/master",
            "review",
            "edx4edx_lite",
            "git@github.com:edx/edx4edx_lite.git",
            status.HTTP_400_BAD_REQUEST,
        ),
        (
            "f6f0acdf746c52e8e73dcc18c4de917a255e5a55dfda902fa2ea2d168b747b37",
            "ref/head/master",
            "push",
            "",
            "git@github.com:edx/edx4edx_lite.git",
            status.HTTP_400_BAD_REQUEST,
        ),
        (
            "116c7b22e18abebc140814dff126697547e3424836dde5f15ddefa8f635af340",
            "ref/head/master",
            "push",
            "edx4edx_lite",
            "",
            status.HTTP_400_BAD_REQUEST,
        ),
    )
    @ddt.unpack
    def test_GitReloadAPIView(
        self,
        signature,
        git_ref,
        event,
        repo_name,
        ssh_url,
        status,
        mocked_get_local_active_branch,
        mocked_get_local_course_repo,
        mocked_add_repo,
    ):
        """
        Test GitReloadAPIView with Signature and Payload
        """
        payload = {
            "repository": {
                "ssh_url": ssh_url,
                "name": repo_name,
            },
            "ref": git_ref,
        }
        response = self.client.post(
            reverse("sysadmin:api:git-reload"),
            payload,
            format="json",
            HTTP_X_Hub_Signature_256=f"sha256={signature}",
            HTTP_X_Github_Event=event,
        )

        self.assertEqual(response.status_code, status)
