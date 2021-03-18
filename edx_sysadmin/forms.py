"""
Forms for edx-sysadmin app
"""

from django import forms


class UserRegistrationForm(forms.Form):
    """
    User Registration form with dynamic fields
    """

    name = forms.CharField(label="Full Name", max_length=100)
    username = forms.CharField(label="Username", max_length=100)
    password = forms.CharField(label="Password", max_length=100)
    email = forms.EmailField(label="Email Address")

    def __init__(self, *args, **kwargs):
        # extra_fields are used to add fields dynamically in the Form depending upon which
        # fields are made "required" in the edX platform through REGISTRATION_EXTRA_FIELDS
        # environment variable
        extra_fields = kwargs.pop("extra_fields", {})

        super().__init__(*args, **kwargs)

        for field, value in extra_fields.items():
            if value["field_type"] == forms.TypedChoiceField:
                self.fields[field] = value["field_type"](choices=value["choices"])
                self.initial[field] = value["choices"][0]
            else:
                self.fields[field] = value["field_type"](initial=value["default_value"])

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data["confirm_email"] = cleaned_data.get("email", "")
        return cleaned_data
