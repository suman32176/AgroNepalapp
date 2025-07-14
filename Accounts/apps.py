from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Accounts'

    def ready(self):
        # Import your signals (keep this)
        import Accounts.signals  
        import Accounts.site_signal

        # Import inside ready(), not at top-level
        try:
            from django.contrib.sites.models import Site
            from django.db.utils import OperationalError, ProgrammingError

            if not Site.objects.exists():
                Site.objects.create(
                    id=1,
                    domain='agronepal-ozxu.onrender.com',
                    name='AgroNepal'
                )
        except (OperationalError, ProgrammingError):
            # Safe to ignore during initial migration
            pass
