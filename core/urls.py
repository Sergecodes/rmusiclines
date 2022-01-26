
from django.urls import path
# from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView
# from graphql_jwt.decorators import jwt_cookie


urlpatterns = [
	# path('graphql/', jwt_cookie(GraphQLView.as_view(graphiql=True))),
	path('graphql/', GraphQLView.as_view(graphiql=True)),
]

