# from django.apps import AppConfig


# class AccountsConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'Accounts'
    
#     def ready(self):
#         """Import signals when the app is ready"""
#         import Accounts.signals  


from django.apps import AppConfig
from django.contrib.sites.models import Site

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Accounts'
    
    def ready(self):
        """Import signals when the app is ready"""
        import Accounts.signals

        # Create or update default Site object
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
        except Exception as e:
            # You can log the error if needed
            pass
