import django_filters
import graphene


class PostFilter(django_filters.FilterSet):
    is_parent = django_filters.BooleanFilter(method='filter_is_parent')

    class Meta:
        filter_fields = {
            'body': ['exact', 'icontains', 'istartswith'],
            'created_on': ['year__exact', 'year__lt', 'year__gt'],
            'is_private': ['exact'],
            'is_simple_repost': ['exact'],
            'parent': ['exact'], 
            'num_ancestor_comments': ['exact', 'lt', 'gt'],
            'num_stars': ['exact', 'lt', 'gt'],
            'num_views': ['exact', 'lt', 'gt'],
        }
        fields = [
            'body', 'created_on', 'is_private', 'is_simple_repost', 'parent',
            'num_ancestor_comments', 'num_stars', 'num_views',
        ]


class CommentFilter(django_filters.FilterSet):
    
    class Meta:
        filter_fields = {
            'body': ['exact', 'icontains', 'istartswith'],
            'created_on': ['year__exact', 'year__lt', 'year__gt'],
            'num_child_comments': ['exact', 'lt', 'gt'],
            'parent': ['exact'],
            'ancestor': ['exact']
        }
        fields = [
            'body', 'created_on', 'num_child_comments', 'parent', 'ancestor'
        ]


class REPOST_TYPE(graphene.Enum):
    SIMPLE_REPOST = 'simple_repost'
    NON_SIMPLE_REPOST = 'non_simple_repost'


class RATING_STARS(graphene.Enum):
    ONE = 1
    THREE = 3
    FIVE = 5


