from django.db.models.signals import post_migrate
from django.contrib.sites.models import Site
from django.dispatch import receiver

@receiver(post_migrate)
def create_or_update_site(sender, **kwargs):
    Site.objects.update_or_create(
        id=1,
        defaults={
            'domain': 'agronepal-ozxu.onrender.com',  # Replace with your domain
            'name': 'AgroNepal'
        }
    )
