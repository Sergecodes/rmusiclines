from django.contrib.auth import get_user_model
from taggit_serializer.serializers import TagListSerializerField, TaggitSerializer
from rest_framework.serializers import ModelSerializer

from accounts.models.artists.models import (
    Artist
)

User = get_user_model()


class UserSerializer(ModelSerializer):
    def create(self, validated_data):
        # pinned_artist_post_id = validated_data.pop('pinned_artist_post')
        # pinned_non_artist_post_id = validated_data.pop('pinned_non_artist_post')
        # user = User(**validated_data)

        # Set relationships
        # user.pinned_artist_post_id = pinned_artist_post_id
        # user.pinned_non_artist_post_id = pinned_non_artist_post_id

        return User.objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        super().update(instance, validated_data)

    class Meta:
        model = User
        # exclude = [
        #     'groups', 'user_permissions'
        # ]
        fields = '__all__'


class ArtistSerializer(ModelSerializer):
    # tags = TagListSerializerField()

    class Meta:
        model = Artist
        fields = '__all__'

