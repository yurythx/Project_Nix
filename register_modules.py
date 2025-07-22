#!/usr/bin/env python
"""
Script para registrar os módulos books, mangas e audiobooks no sistema.
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.config.models.app_module_config import AppModuleConfiguration

def register_modules():
    """Registra os módulos books, mangas e audiobooks."""
    
    modules_to_register = [
        {
            'app_name': 'books',
            'display_name': 'Livros',
            'description': 'Sistema de gerenciamento de livros',
            'url_pattern': 'livros/',
            'menu_icon': 'fas fa-book',
            'menu_order': 30,
            'module_type': 'feature',
            'is_enabled': True,
            'status': 'active'
        },
        {
            'app_name': 'mangas',
            'display_name': 'Mangás',
            'description': 'Sistema de gerenciamento de mangás',
            'url_pattern': 'mangas/',
            'menu_icon': 'fas fa-book-open',
            'menu_order': 40,
            'module_type': 'feature',
            'is_enabled': True,
            'status': 'active'
        },
        {
            'app_name': 'audiobooks',
            'display_name': 'Audiolivros',
            'description': 'Sistema de gerenciamento de audiolivros',
            'url_pattern': 'audiolivros/',
            'menu_icon': 'fas fa-headphones',
            'menu_order': 50,
            'module_type': 'feature',
            'is_enabled': True,
            'status': 'active'
        }
    ]
    
    for module_data in modules_to_register:
        module, created = AppModuleConfiguration.objects.get_or_create(
            app_name=module_data['app_name'],
            defaults=module_data
        )
        
        if created:
            print(f"✅ Módulo '{module_data['display_name']}' registrado com sucesso!")
        else:
            # Atualizar dados existentes
            for key, value in module_data.items():
                setattr(module, key, value)
            module.save()
            print(f"🔄 Módulo '{module_data['display_name']}' atualizado!")
    
    print("\n📊 Módulos ativos no sistema:")
    for module in AppModuleConfiguration.get_enabled_modules():
        status = "🟢 Ativo" if module.status == 'active' else "🟡 Inativo"
        print(f"  {module.menu_icon} {module.display_name} - {status}")

if __name__ == '__main__':
    try:
        register_modules()
        print("\n✨ Registro de módulos concluído com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao registrar módulos: {e}")
        sys.exit(1)
