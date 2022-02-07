import graphene
from graphene_django import DjangoObjectType

from core.utils import PKMixin
from flagging.models.models import Flag, FlagInstance


class FlagNode(PKMixin, DjangoObjectType):
    class Meta:
        model = Flag
        interfaces = [graphene.relay.Node, ]


class FlagInstanceNode(PKMixin, DjangoObjectType):
    class Meta:
        model = FlagInstance
        interfaces = [graphene.relay.Node, ]


