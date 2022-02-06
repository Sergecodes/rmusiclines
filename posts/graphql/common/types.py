import graphene


class REPOST_TYPE(graphene.Enum):
    SIMPLE_REPOST = 'simple_repost'
    NON_SIMPLE_REPOST = 'non_simple_repost'


class RATING_STARS(graphene.Enum):
    ONE = 1
    THREE = 3
    FIVE = 5


