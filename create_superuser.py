import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rental_app.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
email = "vassu_backup@gmail.com"
password = "vassukaju"

user = User.objects.filter(email=email).first()
if user:
    user.set_password(password)
    user.is_staff = True
    user.is_superuser = True
    user.save()
    print(f"✅ Password reset for {email}")
else:
    User.objects.create_superuser(email=email, password=password)
    print(f"✅ Created new superuser {email}")
