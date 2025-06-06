import graphene
from django.contrib.auth import get_user_model
from graphene_django import DjangoObjectType
from graphql_auth.schema import UserNode as BaseUserNode
from graphql_auth.settings import graphql_auth_settings

from accounts.models.users.models import UserType, UserBlocking, UserFollow, Suspension
from core.mixins import GraphenePKMixin

User = get_user_model()


class UserAccountNode(BaseUserNode):
    class Meta:
        model = User
        filter_fields = graphql_auth_settings.USER_NODE_FILTER_FIELDS
        exclude = graphql_auth_settings.USER_NODE_EXCLUDE_FIELDS
        interfaces = (graphene.relay.Node, )


class UserFollowNode(GraphenePKMixin, DjangoObjectType):
    class Meta:
        model = UserFollow
        interfaces = [graphene.relay.Node, ]


class UserTypeNode(GraphenePKMixin, DjangoObjectType):
    class Meta:
        model = UserType
        interfaces = (graphene.relay.Node, )


class UserBlockingNode(GraphenePKMixin, DjangoObjectType):
    class Meta:
        model = UserBlocking
        interfaces = [graphene.relay.Node, ]


class SuspensionNode(GraphenePKMixin, DjangoObjectType):

    # Permit conversion of timedelta 
    def resolve_duration(self, info):
        return self.duration.total_seconds()

    class Meta:
        model = Suspension
        interfaces = [graphene.relay.Node, ]




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

