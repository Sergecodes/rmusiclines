import graphene
from graphene_django import DjangoObjectType

from core.mixins import GraphenePKMixin
from flagging.models.models import Flag, FlagInstance


FlagReason = graphene.Enum.from_enum(FlagInstance.FlagReason)


class FlagNode(GraphenePKMixin, DjangoObjectType):
    class Meta:
        model = Flag
        interfaces = [graphene.relay.Node, ]


class FlagInstanceNode(GraphenePKMixin, DjangoObjectType):
    class Meta:
        model = FlagInstance
        interfaces = [graphene.relay.Node, ]


