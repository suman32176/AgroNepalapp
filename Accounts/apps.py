from django.apps import AppConfig
from django.contrib.sites.models import Site


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Accounts'
    
    def ready(self):
        """Import signals and ensure Site object exists"""
        import Accounts.signals  
        import Accounts.site_signal

        # Create or update the Site object for allauth (no shell needed)
        try:
            Site.objects.update_or_create(
                id=1,
                defaults={
                    'domain': 'agronepal-ozxu.onrender.com',  # ✅ your render domain
                    'name': 'AgroNepal',                      # or any name you prefer
                }
            )
        except Exception as e:
            print(f"[Site creation failed]: {e}")  # Optional: helpful for debugging logs
