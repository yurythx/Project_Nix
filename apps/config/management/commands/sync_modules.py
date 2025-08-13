from django.core.management.base import BaseCommand
from django.conf import settings
from apps.config.services.module_service import ModuleService
from apps.config.models import AppModuleConfiguration
from django.core.management import call_command
import io
import sys


class Command(BaseCommand):
    help = 'Sincroniza módulos com aplicativos instalados'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--test',
            action='store_true',
            help='Executa testes de funcionalidade após sincronização',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força a sincronização mesmo se já estiver atualizado',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostra o que seria feito sem executar',
        )
    
    def handle(self, *args, **options):
        self.stdout.write('🔄 SINCRONIZAÇÃO DE MÓDULOS')
        self.stdout.write('=' * 40)
        
        test_after = options.get('test', False)
        force = options.get('force', False)
        dry_run = options.get('dry_run', False)
        
        if dry_run:
            self.stdout.write('🔍 MODO DRY-RUN (apenas simulação)')
            self.stdout.write('-' * 40)
        
        # 1. Verificar estado atual
        self.check_current_state()
        
        # 2. Executar sincronização
        if not dry_run:
            self.perform_sync(force)
        else:
            self.simulate_sync()
        
        # 3. Executar testes se solicitado
        if test_after and not dry_run:
            self.stdout.write('\n' + '=' * 40)
            self.stdout.write('🧪 EXECUTANDO TESTES DE FUNCIONALIDADE')
            self.stdout.write('=' * 40)
            
            # Capturar saída do comando test_modules
            call_command('test_modules', '--functional-only', stdout=self.stdout)
    
    def check_current_state(self):
        """Verifica o estado atual dos módulos"""
        self.stdout.write('\n📊 ESTADO ATUAL:')
        
        # Módulos no banco
        db_modules = AppModuleConfiguration.objects.all()
        db_count = db_modules.count()
        enabled_count = db_modules.filter(is_enabled=True).count()
        
        # Módulos instalados
        installed_apps = [app for app in settings.INSTALLED_APPS if app.startswith('apps.')]
        installed_count = len(installed_apps)
        
        self.stdout.write(f'  🗄️  Módulos no banco: {db_count}')
        self.stdout.write(f'  🟢 Módulos habilitados: {enabled_count}')
        self.stdout.write(f'  📦 Apps instalados: {installed_count}')
        
        # Verificar diferenças
        db_module_names = set(module.app_name for module in db_modules)
        installed_module_names = set(app.replace('apps.', '') for app in installed_apps)
        
        missing_in_db = installed_module_names - db_module_names
        missing_in_installed = db_module_names - installed_module_names
        
        if missing_in_db:
            self.stdout.write(f'  ⚠️  Não registrados no banco: {list(missing_in_db)}')
        
        if missing_in_installed:
            self.stdout.write(f'  ⚠️  No banco mas não instalados: {list(missing_in_installed)}')
        
        if not missing_in_db and not missing_in_installed:
            self.stdout.write('  ✅ Banco e instalados estão sincronizados')
    
    def simulate_sync(self):
        """Simula a sincronização sem executar"""
        self.stdout.write('\n🔍 SIMULAÇÃO DE SINCRONIZAÇÃO:')
        
        service = ModuleService()
        installed_apps = service.get_installed_apps_list()
        
        for app_name in installed_apps:
            module_name = app_name.replace('apps.', '')
            
            try:
                module = AppModuleConfiguration.objects.get(app_name=module_name)
                self.stdout.write(f'  ℹ️  {module_name}: já existe (seria atualizado se necessário)')
            except AppModuleConfiguration.DoesNotExist:
                is_core = module_name in service.core_apps
                is_enabled = module_name in getattr(settings, 'DEFAULT_ACTIVE_APPS', [])
                
                self.stdout.write(f'  ➕ {module_name}: seria criado (core: {is_core}, enabled: {is_enabled})')
    
    def perform_sync(self, force=False):
        """Executa a sincronização"""
        self.stdout.write('\n🔄 EXECUTANDO SINCRONIZAÇÃO:')
        
        try:
            service = ModuleService()
            
            # Verificar se precisa sincronizar
            if not force:
                installed_apps = service.get_installed_apps_list()
                db_modules = AppModuleConfiguration.objects.all()
                
                db_module_names = set(module.app_name for module in db_modules)
                installed_module_names = set(app.replace('apps.', '') for app in installed_apps)
                
                if db_module_names == installed_module_names:
                    self.stdout.write('  ✅ Módulos já estão sincronizados')
                    return
            
            # Executar sincronização
            result = service.sync_with_installed_apps()
            
            if result:
                self.stdout.write('  ✅ Sincronização concluída com sucesso')
                
                # Mostrar estatísticas atualizadas
                self.check_current_state()
            else:
                self.stdout.write('  ⚠️  Sincronização executada mas sem mudanças')
                
        except Exception as e:
            self.stdout.write(f'  ❌ Erro na sincronização: {e}')
            self.stdout.write('  💡 Tente executar: python manage.py diagnose_modules --fix')