"""
Tests for views
"""
import pytest
import json

from hashlib import sha256
import hmac

from django.conf import settings
from django.http import HttpResponse
from django.test import TestCase, RequestFactory, override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from rest_framework import status

from edx_sysadmin.api.decorators import authenticate_github_request


class AuthenticateGithubRequestTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()

    def test_authenticate_github_request_without_key(self):
        """Test authenticate_github_request decorator without signature key"""

        request = self.factory.post(reverse("sysadmin:api:git-reload"))

        @authenticate_github_request()
        def func(request):
            return HttpResponse("test function")

        response = func(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @override_settings(
        SYSADMIN_GITHUB_WEBHOOK_KEY="nuiVypAArY7lFDgMdyC5kwutDGQdDc6rXljuIcI5iBttpPebui"
    )
    def test_authenticate_github_request_with_invalid_key(self):
        """Test authenticate_github_request decorator with invalid signature key"""

        request = self.factory.post(
            reverse("sysadmin:api:git-reload"),
            data={"data": "demo data"},
            **{
                "HTTP_X_Hub_Signature_256": "sha256=aa3c28d9ec0a5d3c57b5cdf69c90146250ed045f706ad919bc0fa09da197554d"
            },
        )

        @authenticate_github_request()
        def func(request):
            return HttpResponse("test function")

        response = func(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @override_settings(
        SYSADMIN_GITHUB_WEBHOOK_KEY="nuiVypAArY7lFDgMdyC5kwutDGQdDc6rXljuIcI5iBttpPebui"
    )
    def test_authenticate_github_request_with_valid_key(self):
        """Test authenticate_github_request decorator with valid signature key"""

        valid_signature = (
            "173b28e9ec0a5d3c57b5cdf69c90146250ed045f706ad919bc0fa09da197445c"
        )
        request = self.factory.post(
            reverse("sysadmin:api:git-reload"),
            data={"data": "demo data"},
            **{
                "HTTP_X_Hub_Signature_256": f"sha256={valid_signature}",
            },
        )

        @authenticate_github_request()
        def func(request):
            return HttpResponse("test function")

        response = func(request)

        self.assertEqual(response.content, b"test function")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
