from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.config.services.module_service import ModuleService
from apps.config.models.app_module_config import AppModuleConfiguration
import time

User = get_user_model()


class Command(BaseCommand):
    help = 'Demonstra o funcionamento do sistema de módulos'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--interactive',
            action='store_true',
            help='Modo interativo com pausas',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🎭 Demonstração do Sistema de Módulos do Havoc')
        )
        self.stdout.write('=' * 60)
        
        module_service = ModuleService()
        interactive = options.get('interactive', False)
        
        # 1. Mostrar status atual
        self.stdout.write('\n📊 Status Atual dos Módulos:')
        self._show_module_status(module_service)
        
        if interactive:
            input('\nPressione Enter para continuar...')
        
        # 2. Demonstrar desabilitação de módulo
        self.stdout.write('\n🔧 Demonstrando Desabilitação de Módulo:')
        articles_module = module_service.get_module_by_name('articles')
        
        if articles_module and articles_module.is_enabled:
            self.stdout.write(f'  • Desabilitando módulo: {articles_module.display_name}')
            success = module_service.disable_module('articles')
            
            if success:
                self.stdout.write(self.style.SUCCESS('  ✅ Módulo desabilitado com sucesso!'))
                self.stdout.write('  📝 Agora tente acessar /artigos/ - será redirecionado')
            else:
                self.stdout.write(self.style.ERROR('  ❌ Erro ao desabilitar módulo'))
        else:
            self.stdout.write('  ℹ️  Módulo articles já está desabilitado ou não existe')
        
        if interactive:
            input('\nPressione Enter para continuar...')
        
        # 3. Mostrar status após desabilitação
        self.stdout.write('\n📊 Status Após Desabilitação:')
        self._show_module_status(module_service)
        
        if interactive:
            input('\nPressione Enter para continuar...')
        
        # 4. Demonstrar reabilitação
        self.stdout.write('\n🔧 Demonstrando Reabilitação de Módulo:')
        if articles_module:
            self.stdout.write(f'  • Reabilitando módulo: {articles_module.display_name}')
            success = module_service.enable_module('articles')
            
            if success:
                self.stdout.write(self.style.SUCCESS('  ✅ Módulo reabilitado com sucesso!'))
                self.stdout.write('  📝 Agora /artigos/ voltou a funcionar')
            else:
                self.stdout.write(self.style.ERROR('  ❌ Erro ao reabilitar módulo'))
        
        if interactive:
            input('\nPressione Enter para continuar...')
        
        # 5. Status final
        self.stdout.write('\n📊 Status Final dos Módulos:')
        self._show_module_status(module_service)
        
        # 6. Instruções
        self.stdout.write('\n📋 Como Testar:')
        self.stdout.write('  1. Acesse http://localhost:8000/config/modulos/teste/')
        self.stdout.write('  2. Use os botões para habilitar/desabilitar módulos')
        self.stdout.write('  3. Tente acessar URLs dos módulos desabilitados')
        self.stdout.write('  4. Observe as mensagens de redirecionamento')
        
        self.stdout.write('\n🔗 URLs para Testar:')
        self.stdout.write('  • http://localhost:8000/contato/ (pages)')
        self.stdout.write('  • http://localhost:8000/artigos/ (articles)')
        self.stdout.write('  • http://localhost:8000/config/ (config - sempre ativo)')
        
        self.stdout.write(
            self.style.SUCCESS('\n✅ Demonstração concluída!')
        )
    
    def _show_module_status(self, module_service):
        """Mostra o status atual dos módulos"""
        modules = module_service.get_all_modules()
        
        for module in modules:
            status_icon = '🟢' if module.is_available else '🔴'
            core_icon = '🔒' if module.is_core else '📦'
            
            self.stdout.write(
                f'  {status_icon} {core_icon} {module.display_name} ({module.app_name})'
            )
            
            if module.url_pattern:
                url = f'/{module.url_pattern}' if module.url_pattern else '/'
                self.stdout.write(f'    📍 URL: {url}')
            
            if not module.is_available:
                self.stdout.write(f'    ⚠️  Status: {module.status}')
        
        # Estatísticas
        stats = module_service.get_module_statistics()
        self.stdout.write(f'\n  📈 Estatísticas:')
        self.stdout.write(f'    • Total: {stats["total"]}')
        self.stdout.write(f'    • Habilitados: {stats["enabled"]}')
        self.stdout.write(f'    • Principais: {stats["core"]}')
        self.stdout.write(f'    • Personalizados: {stats["custom"]}')
