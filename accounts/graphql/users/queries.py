'''

class UserQuery(graphene.ObjectType):
    all_users = graphene.List(UserType)
    user_by_username = graphene.Field(
        UserType, 
        username=graphene.String(required=True)
    )

    def resolve_all_users(root, info):
        return User.objects.select_related(
            'pinned_non_artist_post',
            'pinned_artist_post'
        ).all()

    def resolve_user_by_username(root, info, username):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None

'''