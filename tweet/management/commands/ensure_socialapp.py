import os
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Ensure Google SocialApp exists and is attached to the Site (useful for production deployments)."

    def handle(self, *args, **options):
        try:
            from django.contrib.sites.models import Site
            from allauth.socialaccount.models import SocialApp
        except Exception as e:
            self.stderr.write(f"Required Django/allauth models not available: {e}")
            return

        client_id = os.getenv("GOOGLE_CLIENT_ID") or ""
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET") or ""
        provider = "google"

        site_id = getattr(settings, "SITE_ID", 1)
        try:
            site = Site.objects.get(id=site_id)
        except Site.DoesNotExist:
            site = Site.objects.create(id=site_id, domain=os.getenv("RENDER_EXTERNAL_HOSTNAME", "rentalpro-web.onrender.com"), name="RentalPro")
            self.stdout.write(f"Created Site id={site_id} domain={site.domain}")

        if not client_id or not client_secret:
            self.stderr.write("GOOGLE_CLIENT_ID and/or GOOGLE_CLIENT_SECRET are not set in the environment.")
            self.stderr.write("Set them and re-run: python manage.py ensure_socialapp")
            return

        app, created = SocialApp.objects.get_or_create(provider=provider, name="Google")
        app.client_id = client_id
        app.secret = client_secret
        app.key = ""
        app.save()

        # Attach to site if not already
        if site not in app.sites.all():
            app.sites.add(site)
            self.stdout.write(f"Attached SocialApp(provider=google) to Site id={site.id} domain={site.domain}")

        if created:
            self.stdout.write(f"Created SocialApp(provider=google) id={app.id}")
        else:
            self.stdout.write(f"Updated SocialApp(provider=google) id={app.id}")

        # Basic config checks
        trusted = getattr(settings, "CSRF_TRUSTED_ORIGINS", [])
        allowed = getattr(settings, "ALLOWED_HOSTS", [])
        self.stdout.write(f"SITE_ID={site_id}; Site.domain={site.domain}")
        self.stdout.write(f"ALLOWED_HOSTS includes rentalpro: {'rentalpro-web.onrender.com' in allowed}")
        self.stdout.write(f"CSRF_TRUSTED_ORIGINS includes rentalpro: {'https://rentalpro-web.onrender.com' in trusted}")
