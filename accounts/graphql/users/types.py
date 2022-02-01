from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from graphene_django import DjangoObjectType
from core.utils import PKMixin

User = get_user_model()


class UserType(PKMixin, DjangoObjectType):
    class Meta:
        model = User



'''
class UserType(DjangoObjectType):
    is_suspended = graphene.Boolean(source='is_suspended')
    can_download = graphene.Boolean(source='can_download')
    can_change_username = graphene.Boolean(source='can_change_username')
    can_change_username_until_date = graphene.Boolean(
        source='can_change_username_until_date'
    )
    # private_artist_posts = graphene.List(source='private_artist_posts')
    private_non_artist_posts = graphene.List(NonArtistPostNode, source='private_non_artist_posts')
    # public_artist_posts
    public_non_artist_posts = graphene.List(NonArtistPostNode, source='public_non_artist_posts')
    # parent_artist_post_comments = 
    # parent_non_artist_post_comments

    class Meta:
        model = User
        exclude = [
            'profile_picture_width', 'profile_picture_height', 
            'cover_photo_width', 'cover_photo_height', 
        ]
'''

