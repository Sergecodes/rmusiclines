from graphql_auth.forms import UpdateAccountForm


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


