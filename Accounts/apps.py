from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Accounts'
    
    def ready(self):
        """Import signals when the app is ready"""
        import Accounts.signals  
