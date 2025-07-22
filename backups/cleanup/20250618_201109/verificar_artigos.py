#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.config.models import AppModuleConfiguration
from apps.config.services.module_service import ModuleService

def verificar_artigos_detalhado():
    print("=== Verificação Detalhada do Módulo de Artigos ===")
    
    # Verificar módulo diretamente
    module = AppModuleConfiguration.objects.filter(app_name='apps.articles').first()
    
    if not module:
        print("❌ Módulo 'apps.articles' não encontrado!")
        
        # Verificar se existe como 'articles'
        module_alt = AppModuleConfiguration.objects.filter(app_name='articles').first()
        if module_alt:
            print(f"✅ Encontrado módulo 'articles': {module_alt}")
            print(f"   - Habilitado: {module_alt.is_enabled}")
            print(f"   - Status: {module_alt.status}")
            print(f"   - Disponível: {module_alt.is_available}")
        else:
            print("❌ Módulo 'articles' também não encontrado!")
            return False
    else:
        print(f"✅ Módulo encontrado: {module}")
        print(f"   - Habilitado: {module.is_enabled}")
        print(f"   - Status: {module.status}")
        print(f"   - Disponível: {module.is_available}")
    
    # Testar com ModuleService
    print("\n=== Testando com ModuleService ===")
    service = ModuleService()
    
    # Testar diferentes nomes de app
    test_apps = ['apps.articles', 'articles', 'artigos']
    
    for app_name in test_apps:
        module_from_service = service.get_module_by_name(app_name)
        is_enabled = service.is_module_enabled(app_name)
        
        print(f"App '{app_name}':")
        print(f"   - Módulo encontrado: {module_from_service is not None}")
        print(f"   - Habilitado: {is_enabled}")
        
        if module_from_service:
            print(f"   - Nome real: {module_from_service.app_name}")
            print(f"   - Disponível: {module_from_service.is_available}")
    
    # Verificar todos os módulos
    print("\n=== Todos os Módulos ===")
    all_modules = AppModuleConfiguration.objects.all()
    for mod in all_modules:
        print(f"- {mod.app_name}: habilitado={mod.is_enabled}, status={mod.status}, disponível={mod.is_available}")
    
    return True

if __name__ == '__main__':
    verificar_artigos_detalhado() 