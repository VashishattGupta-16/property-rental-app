from django.db import migrations
import os

def update_site_domain(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    
    # Use 127.0.0.1:8000 for local development, otherwise use environment variables
    domain = (
        os.getenv("DJANGO_SITE_DOMAIN") or 
        os.getenv("RENDER_EXTERNAL_HOSTNAME") or 
        "127.0.0.1:8000"
    )
    
    Site.objects.update_or_create(
        id=1,
        defaults={
            'domain': domain,
            'name': 'Empire Estate'
        }
    )

class Migration(migrations.Migration):
    dependencies = [
        ('tweet', '0017_alter_customuser_managers_and_more'),
        ('sites', '0002_alter_domain_unique'),
    ]
    operations = [
        migrations.RunPython(update_site_domain),
    ]