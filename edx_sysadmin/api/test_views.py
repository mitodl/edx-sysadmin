"""
Tests for Permissions
"""
import ddt
from unittest.mock import patch

from git import Repo

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status as _status
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
    @override_settings(SYSADMIN_DEFAULT_BRANCH="master")
    @patch(
        "edx_sysadmin.api.views.get_local_active_branch",
        return_value="refs/heads/master",
    )
    @patch("edx_sysadmin.api.views.get_local_course_repo", return_value=Repo())
    @patch("edx_sysadmin.api.views.add_repo")
    @ddt.data(
        (
            "d3a2424a1ad48d8441712400fd75392d56707a7b3e1dc4869239d87ee381cfa9",
            "refs/heads/master",
            "push",
            "edx4edx_lite",
            "git@github.com:edx/edx4edx_lite.git",
            _status.HTTP_200_OK,
        ),
        (
            "dd930da0a34996332e8c983aaeeb9e1cca45cc9b92492f47774d351de4740ddc",
            "refs/heads/master",
            "push",
            "edx4edx_lite",
            "git@github.com:edx/edx4edx_lite.git",
            _status.HTTP_403_FORBIDDEN,
        ),
        (
            "98f48c1b0d35ceec2bfc420f96b76e500b538a6484b17c83c5df4d2c556d8c86",
            "refs/heads/dev",
            "push",
            "edx4edx_lite",
            "git@github.com:edx/edx4edx_lite.git",
            _status.HTTP_400_BAD_REQUEST,
        ),
        (
            "d3a2424a1ad48d8441712400fd75392d56707a7b3e1dc4869239d87ee381cfa9",
            "refs/heads/master",
            "review",
            "edx4edx_lite",
            "git@github.com:edx/edx4edx_lite.git",
            _status.HTTP_400_BAD_REQUEST,
        ),
        (
            "e9b59c215df414f6ba45508912ce6beeb089bdab22ee3fd2e79ebdf42fe2e481",
            "refs/heads/master",
            "push",
            "",
            "git@github.com:edx/edx4edx_lite.git",
            _status.HTTP_400_BAD_REQUEST,
        ),
        (
            "319566e23382c5823ac3483acece8a80644574cf4b35015acd6dc5a82d6ee8b7",
            "refs/heads/master",
            "push",
            "edx4edx_lite",
            "",
            _status.HTTP_400_BAD_REQUEST,
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

    @override_settings(SYSADMIN_GITHUB_WEBHOOK_KEY=SYSADMIN_GITHUB_WEBHOOK_KEY)
    @override_settings(SYSADMIN_DEFAULT_BRANCH="master")
    @patch("edx_sysadmin.api.views.get_local_course_repo", return_value=None)
    @patch("edx_sysadmin.api.views.add_repo")
    @ddt.data(
        (
            "d3a2424a1ad48d8441712400fd75392d56707a7b3e1dc4869239d87ee381cfa9",
            "refs/heads/master",
            "push",
            "edx4edx_lite",
            "git@github.com:edx/edx4edx_lite.git",
            _status.HTTP_200_OK,
        ),
        (
            "d5bd1308cac89ce747cfc93a2679429aa06e179279d912094bac7901e281b783",
            "refs/heads/dummy-test-branch",
            "push",
            "edx4edx_lite",
            "git@github.com:edx/edx4edx_lite.git",
            _status.HTTP_400_BAD_REQUEST,
        ),
        (
            "319566e23382c5823ac3483acece8a80644574cf4b35015acd6dc5a82d6ee8b7",
            "refs/heads/master",
            "push",
            "edx4edx_lite",
            "",
            _status.HTTP_400_BAD_REQUEST,
        ),
    )
    @ddt.unpack
    def test_git_reload_api_view_no_repo(
        self,
        signature,
        git_ref,
        event,
        repo_name,
        ssh_url,
        status,
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
        self.assertTrue(mocked_get_local_course_repo.called_with("repo_name"))

        if response.status_code == _status.HTTP_200_OK:
            self.assertTrue(mocked_add_repo.assert_called)

    # Should return a bad request when "SYSADMIN_DEFAULT_BRANCH" is not configured
    @override_settings(SYSADMIN_GITHUB_WEBHOOK_KEY=SYSADMIN_GITHUB_WEBHOOK_KEY)
    @ddt.data(
        (
            "d3a2424a1ad48d8441712400fd75392d56707a7b3e1dc4869239d87ee381cfa9",
            "refs/heads/master",
            "push",
            "edx4edx_lite",
            "git@github.com:edx/edx4edx_lite.git",
            _status.HTTP_400_BAD_REQUEST,
        ),
    )
    @ddt.unpack
    def test_git_reload_api_view_no_repo_default_branch(
        self,
        signature,
        git_ref,
        event,
        repo_name,
        ssh_url,
        status,
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
