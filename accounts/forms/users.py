from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from graphql_auth.forms import UpdateAccountForm

User = get_user_model()


class ChangeEmailForm(forms.Form):
    """Form used to change a user's email"""
    new_email = forms.EmailField(
        label=_('New email'),
        max_length=50,
        help_text=_('We will send a verification code to this email'),
    )


class UpdateUserForm(UpdateAccountForm):
    """Initialize fields"""

    password = None

    class Meta(UpdateAccountForm.Meta):
        pass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user, fields, data = self.instance, self.fields, self.data

        # Mark fields as not required 
        # for field in fields:
        #     fields[field].required = False

        # If field wasn't passed to form to update user's value for the field
        for field in list(fields.keys()):
            if not data.get(field):
                data[field] = getattr(user, field)


