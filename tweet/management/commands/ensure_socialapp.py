import os
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Ensure Google SocialApp exists and is attached to the Site (useful for production deployments)."

    def handle(self, *args, **options):
        try:
            from django.contrib.sites.models import Site
            from allauth.socialaccount.models import SocialApp
        except Exception as e:
            self.stderr.write(f"Required Django/allauth models not available: {e}")
            return

        client_id = (os.getenv("GOOGLE_CLIENT_ID") or "").strip()
        client_secret = (os.getenv("GOOGLE_CLIENT_SECRET") or "").strip()
        provider = "google"
        render_hostname = (os.getenv("RENDER_EXTERNAL_HOSTNAME") or "").strip()
        is_render = bool(render_hostname)
        site_name = "Empire Estate"

        site_id = getattr(settings, "SITE_ID", 1)
        existing_site_domain = (
            Site.objects.filter(id=site_id).values_list("domain", flat=True).first()
        )
        site_domain = (
            getattr(settings, "PUBLIC_SITE_DOMAIN", "")
            or render_hostname
            or existing_site_domain
            or "127.0.0.1:8000"
        )
        site_url = getattr(settings, "PUBLIC_SITE_URL", f"http://{site_domain}")
        site, created = Site.objects.update_or_create(
            id=site_id,
            defaults={
                "domain": site_domain,
                "name": site_name,
            },
        )
        if created:
            self.stdout.write(f"Created Site id={site_id} domain={site.domain}")
        else:
            self.stdout.write(f"Ensured Site id={site_id} domain={site.domain}")

        if not client_id or not client_secret:
            message = (
                "GOOGLE_CLIENT_ID and/or GOOGLE_CLIENT_SECRET are not set in the environment."
            )
            if is_render:
                raise CommandError(
                    f"{message} Set them in Render, then re-run: python manage.py ensure_socialapp"
                )
            self.stderr.write(message)
            self.stderr.write("Set them and re-run: python manage.py ensure_socialapp")
            return

        # CRITICAL: Clean up duplicate SocialApps to prevent MultipleObjectsReturned at login
        site_apps = SocialApp.objects.filter(provider=provider, sites=site)
        if site_apps.count() > 1:
            to_delete = list(site_apps.values_list("id", flat=True))[1:]
            SocialApp.objects.filter(id__in=to_delete).delete()
            self.stdout.write(f"Deleted {len(to_delete)} duplicate Google SocialApps for site {site.id}")

        app = SocialApp.objects.filter(provider=provider, sites=site).first()

        if app is None:
            # Try finding any Google app to link, or create a new one
            global_apps = SocialApp.objects.filter(provider=provider)
            if global_apps.exists():
                app = global_apps.first()
                # Clean duplicates globally for this provider
                if global_apps.count() > 1:
                    to_delete = list(global_apps.exclude(id=app.id).values_list("id", flat=True))
                    SocialApp.objects.filter(id__in=to_delete).delete()
                    self.stdout.write(f"Cleaned up {len(to_delete)} global duplicate Google SocialApps")
            else:
                app = SocialApp(provider=provider, name="Google")
                self.stdout.write("Creating new Google SocialApp")

        # Sync credentials from environment variables
        if client_id:
            app.client_id = client_id
        if client_secret:
            app.secret = client_secret

        app.key = ""
        if not app.name:
            app.name = "Google"
        app.save()

        # Attach to site if not already
        if site not in app.sites.all():
            app.sites.add(site)
            self.stdout.write(f"Attached SocialApp(provider=google) to Site id={site.id} domain={site.domain}")
        
        self.stdout.write(f"Successfully finalized Google SocialApp id={app.id}")

        # Basic config checks
        trusted = getattr(settings, "CSRF_TRUSTED_ORIGINS", [])
        allowed = getattr(settings, "ALLOWED_HOSTS", [])
        self.stdout.write(f"SITE_ID={site_id}; Site.domain={site.domain}")
        self.stdout.write(
            "ALLOWED_HOSTS includes site domain: "
            f"{any(host == site.domain.split(':')[0] or (host.startswith('.') and site.domain.split(':')[0].endswith(host)) for host in allowed)}"
        )
        is_trusted = site_url in trusted or any(
            (origin.startswith('https://*.') or origin.startswith('http://*.')) and 
            site.domain.split(':')[0].endswith(origin.split('*.')[-1]) for origin in trusted
        )
        self.stdout.write(
            "CSRF_TRUSTED_ORIGINS includes site domain: "
            f"{is_trusted}"
        )
