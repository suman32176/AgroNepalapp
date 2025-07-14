from django.apps import AppConfig

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Accounts'

    def ready(self):
        """Import signals and create/update Site when app is ready"""
        import Accounts.signals

        # Move import inside ready() to avoid AppRegistryNotReady error
        from django.contrib.sites.models import Site

        try:
            site, created = Site.objects.get_or_create(
                id=1,
                defaults={
                    'domain': 'agronepal-ozxu.onrender.com',
                    'name': 'AgroNepal'
                }
            )
            if not created:
                site.domain = 'agronepal-ozxu.onrender.com'
                site.name = 'AgroNepal'
                site.save()
        except Exception:
            pass  # You can log the error if needed
