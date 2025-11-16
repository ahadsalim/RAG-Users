#!/usr/bin/env python
"""Create or update Django superuser"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

email = 'admin@tejarat.chat'
password = 'Admin@123456'

# Delete existing users if exist
User.objects.filter(email=email).delete()
User.objects.filter(username='admin').delete()

# Create new superuser
user = User.objects.create_superuser(
    username='admin',
    email=email,
    password=password,
    first_name='Admin',
    last_name='User'
)

print(f"✅ Superuser created successfully!")
print(f"   Email: {email}")
print(f"   Password: {password}")
print(f"   Login URL: http://admin.tejarat.chat/admin/")
