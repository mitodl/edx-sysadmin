# pylint: disable=import-error
"""
Utility function defined here.
"""
import json

import requests
import six
from common.djangoapps.student.models import UserProfile
from common.djangoapps.util.password_policy_validators import normalize_password
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import Http404
from django.urls import reverse
from django_countries import countries
from xmodule.modulestore.django import modulestore

from edx_sysadmin.utils.markup import HTML

from openedx.core.djangoapps.user_authn.toggles import (  # isort:skip
    is_require_third_party_auth_enabled,
)


User = get_user_model()


def get_course_by_id(course_key, depth=0):
    """
    Given a course id, return the corresponding course descriptor.

    If such a course does not exist, raises a 404.

    depth: The number of levels of children for the modulestore to cache. None means infinite depth
    """
    with modulestore().bulk_operations(course_key):
        course = modulestore().get_course(course_key, depth=depth)
    if course:
        return course
    else:
        raise Http404("Course not found: {}.".format(six.text_type(course_key)))


def get_registration_required_extra_fields():
    """
    It processes and returns a list of extra fields which are required for User account
    registration through Registration API "/user_api/v1/account/registration/", depending
    upon "settings.REGISTRATION_EXTRA_FIELDS" environment setting

    Arguments:
    None

    Returns:
    extra_fields (list) - list of required fields from "settings.REGISTRATION_EXTRA_FIELDS"
    """
    extra_fields = []
    for field, status in settings.REGISTRATION_EXTRA_FIELDS.items():
        if status == "required":
            extra_fields.append(field)
    return extra_fields


def get_registeration_required_extra_fields_with_values():
    """
    It maps registration required extra fields with some pre-defined default values to create
    django form fields dynamically

    Arguments:
    None

    Returns:
    extra_fields (dict) - contains all required fields and their mapping with default values
    and form type.
    {
        ...
        "FIELD_NAME": {
            "field_type": "FIELD_TYPE",
            "default_value": "DEFAULT_VALUE",     # if applicable
            "choices": "LIST_OF_OPTIONS"          # if applicable
        }
        ...
    }

    """
    # importing here due to circular import
    from edx_sysadmin.constants import (  # pylint: disable=import-outside-toplevel; isort:skip
    FIELDS_AND_DEFAULT_VALUES_MAP,
    )

    extra_fields = {}

    # If Registration API is not functional we can't use it, so no need to process extra fields
    if is_registration_api_functional():
        for field in get_registration_required_extra_fields():
            mapping = FIELDS_AND_DEFAULT_VALUES_MAP.get(field)
            if mapping:
                extra_fields[field] = mapping
    return extra_fields


def is_registration_api_functional():
    """
    Checks if User Registration API "/user_api/v1/account/registration/" is functional or not
    depending upon two environemnt variables "settings.FEATURES['ALLOW_PUBLIC_ACCOUNT_CREATION']"
    and "settings.ENABLE_REQUIRE_THIRD_PARTY_AUTH"

    Arguments:
    None

    Returns:
    Boolean - True if User Registration API "/user_api/v1/account/registration/" is functional
    """
    if (
        settings.FEATURES["ALLOW_PUBLIC_ACCOUNT_CREATION"]
        and not is_require_third_party_auth_enabled()
    ):
        return True
    return False


def create_user_account(data, build_absolute_uri, use_reg_api=True):
    """
    Create User Account through "/user_api/v1/account/registration/" API (if available)
    or directly through "User" and "UserProfile" models

    Arguments:
    data (dict) - the params to use while creating user account, it can have "username", "name",
        "email", "password" and many other registration related fields

    build_absolute_uri (method|request.build_absolute_uri) - a request method to build
        absolute uri

    use_reg_api (boolean) - used to specify which account creation flow should be followed

    Returns:
    context (dict) - having context to be passed to templates having information about success and
        failure of account creation
    """
    context = {}
    if is_registration_api_functional() and use_reg_api:
        context = make_reg_api_request(
            build_absolute_uri(reverse("user_api_registration")), data=data
        )
    else:
        context = create_user_through_db_models(data)

    return context


def create_user_through_db_models(data):
    """
    It Registers User through database models

    Arguments:
    data (dict) - User account details

    Returns:
    context (dict) - context to be passed to templates having information about success and
        failure of account creation
    """
    context = {}
    try:
        if not User.objects.filter(email=data["email"]).exists():
            user = User(username=data["username"], email=data["email"], is_active=True)
            password = normalize_password(data["password"])
            user.set_password(password)
            user.save()

            profile = UserProfile(user=user)
            profile.name = data.get("name")
            profile.save()

            context["success_message"] = HTML(
                f"A new account has been registered for user: {data['username']}"
            )
        else:
            context["error_message"] = HTML(
                f"An account with email: {data['email']} already exists"
            )
            return context
    except Exception as err:  # pylint: disable=broad-except
        context["error_message"] = HTML(
            f"Account couldn't be created due to following error: {err}"
        )

    return context


def make_reg_api_request(api_endpoint, data):
    """
    Make POST request to "/user_api/v1/account/registration/" API to register User

    Arguments:
    api_endpoint (url) - An absolute url to registration API

    data (dict) - User account details

    Returns:
    context (dict) - context to be passed to templates having information about success and
        failure of account creation
    """
    context = {}

    resp = requests.post(api_endpoint, data=data)

    if resp.status_code == 200:
        context["success_message"] = HTML(
            f"A new account has been registered through API for user: {data.get('username')}"
        )
    else:
        context["error_message"] = HTML(
            f"Account couldn't be created due to following error(s): {transform_error_message(resp.content)}"
        )

    return context


def transform_error_message(resp_content):
    """
    It transforms Registration API error messages

    Arguments:
    resp_content (response.content) - Response object's content

    Returns:
    message (str) - A string of formatted errors
    """
    content = json.loads(resp_content.decode("utf-8").replace("\n", ""))
    message = ""
    for error_key, error_content in content.items():
        if len(error_content):
            message += f"<li>{error_key}: {error_content[0].get('user_message')}</li>"
    return f"<ul>{message}</ul>"


def get_level_of_education_choices():
    """
    List of "Level of Education" choices provided by UserProfile
    """
    return [
        (name, label) for name, label in UserProfile.LEVEL_OF_EDUCATION_CHOICES
    ]  # pylint: disable=unnecessary-comprehension


def get_gender_choices():
    """
    List of "Gender" choices provided by UserProfile
    """
    return [
        (name, label) for name, label in UserProfile.GENDER_CHOICES
    ]  # pylint: disable=unnecessary-comprehension


def get_valid_year_of_birth_choices():
    """
    List of valid "Year of Birth" choices provided by UserProfile
    """
    return [
        (six.text_type(year), six.text_type(year)) for year in UserProfile.VALID_YEARS
    ]


def get_country_choices():
    """
    List of "Country" choices
    """
    return list(countries)
