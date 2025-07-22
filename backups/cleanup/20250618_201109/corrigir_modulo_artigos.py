#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.config.models import AppModuleConfiguration

def corrigir_modulo_artigos():
    print("=== Verificando Módulo de Artigos ===")
    
    # Verificar configuração do módulo
    module = AppModuleConfiguration.objects.filter(app_name='apps.articles').first()
    
    if not module:
        print("❌ Módulo de artigos não encontrado!")
        return False
    
    print(f"📋 Módulo encontrado: {module.display_name}")
    print(f"🔧 Status atual: {module.status}")
    print(f"✅ Habilitado: {module.is_enabled}")
    
    # Verificar se o módulo está habilitado
    if not module.is_enabled:
        print("\n🔄 Habilitando módulo de artigos...")
        module.is_enabled = True
        module.status = 'active'
        module.save()
        print("✅ Módulo habilitado com sucesso!")
    else:
        print("✅ Módulo já está habilitado!")
    
    # Verificar se o status está correto
    if module.status != 'active':
        print(f"\n🔄 Corrigindo status do módulo...")
        module.status = 'active'
        module.save()
        print("✅ Status corrigido para 'active'!")
    
    print(f"\n📊 Status final:")
    print(f"   - Habilitado: {module.is_enabled}")
    print(f"   - Status: {module.status}")
    print(f"   - URL: /artigos/")
    
    return True

if __name__ == '__main__':
    sucesso = corrigir_modulo_artigos()
    if sucesso:
        print("\n🎉 Módulo de artigos está funcionando corretamente!")
        print("🌐 Acesse: http://localhost:8000/artigos/")
    else:
        print("\n❌ Erro ao corrigir módulo de artigos!") 