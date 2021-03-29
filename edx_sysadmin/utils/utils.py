# pylint: disable=import-error
"""
Utility function defined here.
"""
import json
import urllib.parse
import requests

from django_countries import countries

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import Http404
from django.urls import reverse
from django.utils.translation import ugettext as _

from common.djangoapps.student.models import UserProfile
from common.djangoapps.util.password_policy_validators import normalize_password
from openedx.core.djangoapps.user_authn.toggles import (
    is_require_third_party_auth_enabled,
)
from xmodule.modulestore.django import modulestore

from edx_sysadmin.utils.markup import HTML, Text


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
        raise Http404(f"{_('Course not found')}: {course_key}")


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


def get_registration_required_extra_fields_with_values():
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
    extra_fields = {}

    # If Registration API is not functional we can't use it, so no need to process extra fields
    if is_registration_api_functional():
        fields_and_default_values_map = get_fields_and_default_values_map()
        for field in get_registration_required_extra_fields():
            mapping = fields_and_default_values_map.get(field)
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


def create_user_account(data, use_reg_api=True):
    """
    Create User Account through "/user_api/v1/account/registration/" API (if available)
    or directly through "User" and "UserProfile" models

    Arguments:
    data (dict) - the params to use while creating user account, it can have "username", "name",
        "email", "password" and many other registration related fields

    use_reg_api (boolean) - used to specify which account creation flow should be followed

    Returns:
    context (dict) - having context to be passed to templates having information about success and
        failure of account creation
    """
    context = {}
    if is_registration_api_functional() and use_reg_api:
        context = make_reg_api_request(data=data)
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

            context[
                "success_message"
            ] = f"{_('A new account has been registered for user')}: {data['username']}"
        else:
            context[
                "error_message"
            ] = f"{_('An account already exists with email')}: {data['email']}"
            return context
    except Exception as err:  # pylint: disable=broad-except
        context[
            "error_message"
        ] = f"{_('Account could not be created due to following error')}: {err}"

    return context


def make_reg_api_request(data):
    """
    Make POST request to "/user_api/v1/account/registration/" API to register User

    Arguments:
    data (dict) - User account details

    Returns:
    context (dict) - context to be passed to templates having information about success and
        failure of account creation
    """
    context = {}

    api_endpoint = urllib.parse.urljoin(
        get_lms_root_url(), reverse("user_api_registration")
    )
    resp = requests.post(api_endpoint, data=data)

    if resp.status_code == 200:
        context[
            "success_message"
        ] = f"{_('A new account has been registered through API for user')}: {data.get('username')}"
    else:
        context[
            "error_message"
        ] = f"{_('Account could not be created due to following error(s)')}: {transform_error_message(resp.content)}"

    return context


def get_lms_root_url():
    """
    It returns LMS Root URL of edx-platform

    Returns:
    url (str) - LMS Root URL
    """
    return settings.LMS_ROOT_URL


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
        if error_content:
            error_message = (
                str(error_content[0].get("user_message"))
                if isinstance(error_content, list)
                else error_content
            )
            message += Text("{li_start} {error_key}: {error_content} {li_end}").format(
                li_start=HTML("<li>"),
                error_key=error_key,
                error_content=error_message,
                li_end=HTML("</li>"),
            )
    return Text("{ul_start} {message} {ul_end}").format(
        ul_start=HTML("<ul>"), message=message, ul_end=HTML("</ul>")
    )


def get_level_of_education_choices():
    """
    List of "Level of Education" choices provided by UserProfile
    """
    return list(UserProfile.LEVEL_OF_EDUCATION_CHOICES)


def get_gender_choices():
    """
    List of "Gender" choices provided by UserProfile
    """
    return list(UserProfile.GENDER_CHOICES)


def get_valid_year_of_birth_choices():
    """
    List of valid "Year of Birth" choices provided by UserProfile
    """
    return [(year, year) for year in UserProfile.VALID_YEARS]


def get_country_choices():
    """
    List of "Country" choices
    """
    return list(countries)


def get_fields_and_default_values_map():
    """
    It maps registration required extra fields with some pre-defined default values

    Arguments:
    None

    Returns:
    fields_and_default_values_map (dict) - contains all required fields and their mapping with default values
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
    return {
        "level_of_education": {
            "field_type": forms.TypedChoiceField,
            "choices": get_level_of_education_choices(),
        },
        "gender": {
            "field_type": forms.TypedChoiceField,
            "choices": get_gender_choices(),
        },
        "year_of_birth": {
            "field_type": forms.TypedChoiceField,
            "choices": get_valid_year_of_birth_choices(),
        },
        "mailing_address": {
            "field_type": forms.CharField,
            "default_value": "This is the default Mailing Address",
        },
        "goals": {
            "field_type": forms.CharField,
            "default_value": "This is the default Goal",
        },
        "honor_code": {"field_type": forms.BooleanField, "default_value": True},
        "terms_of_service": {"field_type": forms.BooleanField, "default_value": True},
        "city": {"field_type": forms.CharField, "default_value": "Kabul"},
        "country": {
            "field_type": forms.TypedChoiceField,
            "choices": get_country_choices(),
        },
    }
