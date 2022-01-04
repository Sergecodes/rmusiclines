from django.db import connections
from django.test.runner import DiscoverRunner
from types import MethodType


SCHEMAS = [
    'django', 'accounts', 'flagging', 
    'posts', 'notifications', 'subscriptions'
]

def prepare_database(self):
    self.connect()
    for schema in SCHEMAS:
        self.connection.cursor().execute(
            f"""
            CREATE SCHEMA {schema} AUTHORIZATION sergeman;
            GRANT ALL ON SCHEMA {schema} TO sergeman;
            """
        )
    self.connection.cursor().execute(
        """
        SET search_path TO django,accounts,flagging,posts,notifications,subscriptions;
        """
    )
    


class PostgresSchemaTestRunner(DiscoverRunner):
    def setup_databases(self, **kwargs):
        for connection_name in connections:
            connection = connections[connection_name]
            connection.prepare_database = MethodType(prepare_database, connection)

        return super().setup_databases(**kwargs)

