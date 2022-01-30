from django import forms
from django.contrib.auth import get_user_model
from graphql_auth.forms import UpdateAccountForm

User = get_user_model()


class ChangeUsernameForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', )


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


