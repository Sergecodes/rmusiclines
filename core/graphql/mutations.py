"""For common / core mutations"""

import graphene
from django.core.cache import cache
from graphql_auth.bases import Output
from graphene_file_upload.scalars import Upload

from core.constants import FILE_STORAGE_CLASS
from core.decorators import verification_and_login_required

STORAGE = FILE_STORAGE_CLASS()


class UploadMutation(graphene.Mutation, Output):
    class Arguments:
        file = Upload(required=True)

    # Apparently this should be an instance method not a class method
    @verification_and_login_required
    def mutate(self, info, file, **kwargs):
        print(self)
        print(info)
        print(file, type(file))
        print(kwargs)

        return UploadMutation(success=True)




