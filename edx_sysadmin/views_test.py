"""
Tests for views
"""
import pytest

pytestmark = [pytest.mark.django_db]


def test_initial_fake_test():
    """
    Fake test for initial test configurations
    """
    assert True is True  # pylint: disable=comparison-with-itself
