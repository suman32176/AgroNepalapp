from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Accounts'

    def ready(self):
        # Import your signals (keep this)
        import Accounts.signals  
        import Accounts.site_signal

       
