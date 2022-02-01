
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from graphene_file_upload.django import FileUploadGraphQLView
from graphql_jwt.decorators import jwt_cookie


urlpatterns = [
	# Using this jwt_cookie decorator, we no longer need to pass the Authorization
	# header to the request; a cookie will be automatically used to store the
	# authed user's token.
	# path('graphql/', jwt_cookie(FileUploadGraphQLView.as_view(graphiql=True))),
	path('graphql/', jwt_cookie(csrf_exempt(FileUploadGraphQLView.as_view(graphiql=True)))),
]

