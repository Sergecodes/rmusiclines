from django.core.files.uploadedfile import SimpleUploadedFile
from graphene_file_upload.django.testing import GraphQLFileUploadTestCase


class MutationTestCase(GraphQLFileUploadTestCase):
   def test_some_mutation(self):
        test_file = SimpleUploadedFile(name='test.txt', content=file_text.encode('utf-8'))

        response = self.file_query(
            '''
            mutation testMutation($file: Upload!) {
                myUpload(fileIn: $file) {
                    ok
                }
            }
            ''',
            op_name='testMutation',
            files={'file': test_file},
        )

        # This validates the status code and if you get errors
        self.assertResponseNoErrors(response)

