from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.sites.models import Site

@receiver(post_migrate)
def create_or_update_site(sender, **kwargs):
    Site.objects.update_or_create(
        domain='agronepal-ozxu.onrender.com',
        defaults={
            'name': 'AgroNepal'
        }
    )
