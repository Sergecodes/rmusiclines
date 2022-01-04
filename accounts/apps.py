from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        import accounts.signals
        from actstream import registry

        registry.register(self.get_model('Artist'))
        registry.register(self.get_model('User'))
        registry.register(self.get_model('ArtistFollow'))
        # registry.register(self.get_model('UserBlocking'))
        # registry.register(self.get_model('UserFollow'))
