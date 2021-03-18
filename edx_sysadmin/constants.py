"""
Constants for edx_sysadmin
"""

from django import forms

from edx_sysadmin.utils.markup import HTML
from edx_sysadmin.utils.utility import (
    get_country_choices,
    get_gender_choices,
    get_level_of_education_choices,
    get_valid_year_of_birth_choices,
)


FIELDS_AND_DEFAULT_VALUES_MAP = {
    # Pattern of Fields Mapping
    # "FIELD_NAME": {
    #   "field_type": "FIELD_TYPE",
    #   "default_value": "DEFAULT_VALUE",
    #   "choices": "LIST_OF_OPTIONS"
    # }
    "level_of_education": {
        "field_type": forms.TypedChoiceField,
        "choices": get_level_of_education_choices(),
    },
    "gender": {"field_type": forms.TypedChoiceField, "choices": get_gender_choices()},
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
    "country": {"field_type": forms.TypedChoiceField, "choices": get_country_choices()},
}
