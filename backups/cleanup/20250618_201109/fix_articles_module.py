#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.config.models import AppModuleConfiguration
from apps.accounts.models import User

def fix_articles_module():
    print("=== Fixing Articles Module ===")
    
    # Get or create admin user
    admin_user, created = User.objects.get_or_create(
        email='admin@fireflies.com',
        defaults={
            'username': 'admin',
            'first_name': 'Admin',
            'last_name': 'User',
            'is_staff': True,
            'is_superuser': True
        }
    )
    
    # Get the articles module
    module = AppModuleConfiguration.objects.filter(app_name='apps.articles').first()
    
    if module:
        print(f"Found module: {module.display_name}")
        print(f"Current enabled: {module.is_enabled}")
        print(f"Current status: {module.status}")
        
        # Enable the module
        module.is_enabled = True
        module.status = 'active'
        module.updated_by = admin_user
        module.save()
        
        print(f"✅ Module enabled and status set to active")
        return True
    else:
        print("❌ Module not found!")
        return False

if __name__ == '__main__':
    success = fix_articles_module()
    if success:
        print("\n✅ Articles module is now enabled!")
    else:
        print("\n❌ Failed to enable articles module!") 