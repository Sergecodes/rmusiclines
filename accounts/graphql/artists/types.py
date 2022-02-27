import django_filters
import graphene
from django.db.models import Q
from functools import reduce
from graphene_django import DjangoObjectType

from accounts.models.artists.models import Artist, ArtistPhoto, ArtistFollow
from core.mixins import GraphenePKMixin, GraphenePhotoMixin, GrapheneRenderTaggitTags


class ArtistFilter(django_filters.FilterSet):
    tags = django_filters.CharFilter(method='filter_tags')

    class Meta:
        model = Artist
        filter_fields = {
            'name': ['exact', 'icontains', 'istartswith'],
            'gender': ['exact'],
            'num_followers': ['exact', 'lt', 'gt'],
            'num_posts': ['exact', 'lt', 'gt'],
            'country': ['exact'],
            'tags': ['exact']
        }
        fields = ['name', 'gender', 'num_followers', 'num_posts', 'country', 'tags']

    def filter_tags(self, queryset, name, value: str):
        tag_list = value.split()
        qs = queryset.filter(
            reduce(
                lambda x, y: x | y, 
                [Q(tags__name__icontains=word) for word in tag_list]
            )
        )
        return qs


class ArtistNode(GraphenePKMixin, GrapheneRenderTaggitTags, DjangoObjectType):
    class Meta:
        model = Artist
        interfaces = [graphene.relay.Node, ]
        filterset_class = ArtistFilter


class ArtistPhotoNode(GraphenePKMixin, GraphenePhotoMixin, DjangoObjectType):
    class Meta:
        model = ArtistPhoto
        interfaces = [graphene.relay.Node, ]


class ArtistFollowNode(GraphenePKMixin, DjangoObjectType):
    class Meta:
        model = ArtistFollow
        interfaces = [graphene.relay.Node, ]

