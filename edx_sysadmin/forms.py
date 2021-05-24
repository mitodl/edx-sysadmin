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
    password = forms.CharField(
        label="Password", widget=forms.PasswordInput, max_length=100
    )
    email = forms.EmailField(label="Email Address")

    def __init__(self, *args, **kwargs):
        """
        Overrides __init__ method to add dynamic fields in the form

        Arguments:
        kwargs["extra_fields"] (dict) - Contains data regarding the fields we want to get
        added dynamically to form depending upon which fields are made "required" in the edX platform
        through REGISTRATION_EXTRA_FIELDS environment variable
        """

        extra_fields = kwargs.pop("extra_fields", {})

        super().__init__(*args, **kwargs)

        for field, value in extra_fields.items():
            if value["field_type"] == forms.TypedChoiceField:
                self.fields[field] = value["field_type"](choices=value["choices"])
                self.initial[field] = value["choices"][0]
            else:
                self.fields[field] = value["field_type"](initial=value["default_value"])

    def clean(self):
        """
        Overrides clean method to add "confirm_email" to "cleaned_data"
        """
        cleaned_data = super().clean()
        cleaned_data["confirm_email"] = cleaned_data.get("email", "")
        return cleaned_data
