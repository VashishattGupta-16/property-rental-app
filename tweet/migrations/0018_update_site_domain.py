from django.db import migrations
import os

def update_site_domain(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    # Use Render's env var or fallback to the Render domain
    domain = os.getenv("RENDER_EXTERNAL_HOSTNAME", "theresidenceco-web.onrender.com")
    # Replace '1' with your SITE_ID if different
    Site.objects.update_or_create(
        id=1,
        defaults={
            'domain': domain,
            'name': 'Empire Estate'
        }
    )

class Migration(migrations.Migration):
    dependencies = [
        ('tweet', '0017_alter_customuser_managers_and_more'), # Ensure this matches your last migration
        ('sites', '0002_alter_domain_unique'),
    ]
    operations = [
        migrations.RunPython(update_site_domain),
    ]