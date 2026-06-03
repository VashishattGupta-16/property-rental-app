from django.db import migrations
import os

def update_site_domain(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    
    # Render automatically provides RENDER_EXTERNAL_HOSTNAME (e.g. myapp.onrender.com)
    domain = os.getenv("RENDER_EXTERNAL_HOSTNAME")
    
    if domain:
        # Update the site domain only if we are in a production/Render environment
        Site.objects.update_or_create(
            id=1,
            defaults={
                'domain': domain,
                'name': 'Empire Estate'
            }
        )
    # Locally, we rely on the default (example.com) or manual adjustment in Admin

class Migration(migrations.Migration):
    dependencies = [
        ('tweet', '0017_alter_customuser_managers_and_more'), # Ensure this matches your last migration
        ('sites', '0002_alter_domain_unique'),
    ]
    operations = [
        migrations.RunPython(update_site_domain),
    ]