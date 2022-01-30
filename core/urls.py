
from django.urls import path
# from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView
from graphql_jwt.decorators import jwt_cookie


urlpatterns = [
	# Using this jwt_cookie decorator, we no longer need to pass the Authorization
	# header to the request; a cookie will be automatically used to store the
	# authed user's token.
	path('graphql/', jwt_cookie(GraphQLView.as_view(graphiql=True))),
	# path('graphql/', GraphQLView.as_view(graphiql=True)),
]

