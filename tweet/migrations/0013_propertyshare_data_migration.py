# tweet/migrations/0013_fix_phone_number_manually.py

from django.db import migrations

class Migration(migrations.Migration):

    # This migration must run after all your other 'tweet' migrations.
    # Update '0012_...' to the actual name of your last migration file.
    dependencies = [
        ('tweet', '0012_propertyshare_data_migration'),
    ]

    operations = [
        # This operation explicitly and safely alters the column type in PostgreSQL.
        # It is a metadata-only change and will not cause a table rewrite for this conversion.
        migrations.RunSQL(
            "ALTER TABLE tweet_customuser ALTER COLUMN phone_number TYPE varchar(15);",
            reverse_sql="ALTER TABLE tweet_customuser ALTER COLUMN phone_number TYPE varchar(10);",
        ),
    ]
