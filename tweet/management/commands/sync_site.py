from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Sync the Django Sites entry with PUBLIC_SITE_DOMAIN'

    def handle(self, *args, **kwargs):
        domain = settings.PUBLIC_SITE_DOMAIN
        site_id = settings.SITE_ID
        site, created = Site.objects.update_or_create(
            id=site_id,
            defaults={'domain': domain, 'name': 'Empire Estate'},
        )
        action = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(f'{action} site: {domain}'))
