from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model
from apps.config.models import AppModuleConfiguration
from apps.config.services.module_service import ModuleService
import sys

User = get_user_model()


class Command(BaseCommand):
    help = 'Diagnostica problemas no sistema de gerenciamento de módulos'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Tenta corrigir problemas encontrados automaticamente',
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Email do usuário para testar permissões',
        )
    
    def handle(self, *args, **options):
        self.stdout.write('🔍 DIAGNÓSTICO DO SISTEMA DE MÓDULOS')
        self.stdout.write('=' * 50)
        
        fix_mode = options.get('fix', False)
        user_email = options.get('user')
        
        # 1. Verificar configuração básica
        self.check_basic_config()
        
        # 2. Verificar módulos no banco
        self.check_modules_database()
        
        # 3. Verificar middlewares
        self.check_middlewares()
        
        # 4. Verificar URLs
        self.check_urls()
        
        # 5. Verificar permissões de usuário
        if user_email:
            self.check_user_permissions(user_email)
        
        # 6. Verificar ModuleService
        self.check_module_service()
        
        # 7. Tentar corrigir problemas se solicitado
        if fix_mode:
            self.fix_common_problems()
        
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write('✅ Diagnóstico concluído!')
    
    def check_basic_config(self):
        """Verifica configuração básica"""
        self.stdout.write('\n📋 1. CONFIGURAÇÃO BÁSICA:')
        
        # Verificar INSTALLED_APPS
        installed_apps = getattr(settings, 'INSTALLED_APPS', [])
        if 'apps.config' in installed_apps:
            self.stdout.write('  ✅ apps.config está em INSTALLED_APPS')
        else:
            self.stdout.write('  ❌ apps.config NÃO está em INSTALLED_APPS')
        
        # Verificar apps locais
        local_apps = ['apps.accounts', 'apps.pages', 'apps.articles']
        for app in local_apps:
            if app in installed_apps:
                self.stdout.write(f'  ✅ {app} está instalado')
            else:
                self.stdout.write(f'  ⚠️  {app} não está instalado')
    
    def check_modules_database(self):
        """Verifica módulos no banco de dados"""
        self.stdout.write('\n🗄️ 2. MÓDULOS NO BANCO DE DADOS:')
        
        try:
            modules = AppModuleConfiguration.objects.all()
            total = modules.count()
            enabled = modules.filter(is_enabled=True).count()
            available = modules.filter(is_enabled=True, status='active').count()
            
            self.stdout.write(f'  📊 Total de módulos: {total}')
            self.stdout.write(f'  🟢 Módulos habilitados: {enabled}')
            self.stdout.write(f'  ✅ Módulos disponíveis: {available}')
            
            if total == 0:
                self.stdout.write('  ⚠️  Nenhum módulo encontrado - sistema precisa ser inicializado')
                return False
            
            # Listar módulos
            for module in modules:
                status = "🟢 ATIVO" if module.is_enabled else "🔴 INATIVO"
                available_status = "✅ DISPONÍVEL" if module.is_available else "❌ INDISPONÍVEL"
                self.stdout.write(f'    - {module.app_name}: {status} | {available_status}')
            
            return True
            
        except Exception as e:
            self.stdout.write(f'  ❌ Erro ao acessar banco: {e}')
            return False
    
    def check_middlewares(self):
        """Verifica middlewares"""
        self.stdout.write('\n🔧 3. MIDDLEWARES:')
        
        middleware = getattr(settings, 'MIDDLEWARE', [])
        
        required_middlewares = [
            'apps.config.middleware.module_middleware.ModuleAccessMiddleware',
            'apps.config.middleware.module_middleware.ModuleContextMiddleware',
        ]
        
        for mw in required_middlewares:
            if mw in middleware:
                self.stdout.write(f'  ✅ {mw.split(".")[-1]} está ativo')
            else:
                self.stdout.write(f'  ❌ {mw.split(".")[-1]} NÃO está ativo')
    
    def check_urls(self):
        """Verifica URLs"""
        self.stdout.write('\n🌐 4. URLS:')
        
        try:
            from django.urls import reverse
            
            # Testar URLs principais
            test_urls = [
                ('config:dashboard', '/config/'),
                ('config:module_list', '/config/modulos/'),
                ('config:user_list', '/config/usuarios/'),
                ('config:email_config', '/config/email/'),
                ('config:system_config', '/config/sistema/'),
            ]
            
            for url_name, expected_path in test_urls:
                try:
                    actual_path = reverse(url_name)
                    if actual_path == expected_path:
                        self.stdout.write(f'  ✅ {url_name}: {actual_path}')
                    else:
                        self.stdout.write(f'  ⚠️  {url_name}: {actual_path} (esperado: {expected_path})')
                except Exception as e:
                    self.stdout.write(f'  ❌ {url_name}: Erro - {e}')
                    
        except Exception as e:
            self.stdout.write(f'  ❌ Erro ao verificar URLs: {e}')
    
    def check_user_permissions(self, user_email):
        """Verifica permissões do usuário"""
        self.stdout.write(f'\n👤 5. PERMISSÕES DO USUÁRIO ({user_email}):')
        
        try:
            user = User.objects.get(email=user_email)
            
            self.stdout.write(f'  📧 Email: {user.email}')
            self.stdout.write(f'  👤 Nome: {user.get_full_name() or user.username}')
            self.stdout.write(f'  🔐 Ativo: {"Sim" if user.is_active else "Não"}')
            self.stdout.write(f'  👑 Staff: {"Sim" if user.is_staff else "Não"}')
            self.stdout.write(f'  🦸 Superuser: {"Sim" if user.is_superuser else "Não"}')
            
            # Verificar se pode acessar config
            can_access_config = user.is_staff or user.is_superuser
            if can_access_config:
                self.stdout.write('  ✅ Pode acessar painel de configuração')
            else:
                self.stdout.write('  ❌ NÃO pode acessar painel de configuração')
                self.stdout.write('    💡 Usuário precisa ser staff ou superuser')
            
        except User.DoesNotExist:
            self.stdout.write(f'  ❌ Usuário {user_email} não encontrado')
        except Exception as e:
            self.stdout.write(f'  ❌ Erro ao verificar usuário: {e}')
    
    def check_module_service(self):
        """Verifica ModuleService"""
        self.stdout.write('\n⚙️ 6. MODULE SERVICE:')
        
        try:
            service = ModuleService()
            
            # Testar métodos principais
            all_modules = service.get_all_modules()
            enabled_modules = service.get_enabled_modules()
            available_modules = service.get_available_modules()
            menu_modules = service.get_menu_modules()
            
            self.stdout.write(f'  📊 get_all_modules(): {len(all_modules)} módulos')
            self.stdout.write(f'  🟢 get_enabled_modules(): {len(enabled_modules)} módulos')
            self.stdout.write(f'  ✅ get_available_modules(): {len(available_modules)} módulos')
            self.stdout.write(f'  📋 get_menu_modules(): {len(menu_modules)} módulos')
            
            # Testar módulos específicos
            test_modules = ['accounts', 'config', 'pages', 'articles']
            for module_name in test_modules:
                is_enabled = service.is_module_enabled(module_name)
                is_core = service.is_core_module(module_name)
                status = "🟢 ATIVO" if is_enabled else "🔴 INATIVO"
                core_status = "⭐ CORE" if is_core else ""
                self.stdout.write(f'    - {module_name}: {status} {core_status}')
            
        except Exception as e:
            self.stdout.write(f'  ❌ Erro no ModuleService: {e}')
    
    def fix_common_problems(self):
        """Tenta corrigir problemas comuns"""
        self.stdout.write('\n🔧 7. CORRIGINDO PROBLEMAS:')
        
        try:
            # Inicializar sistema de módulos se necessário
            if AppModuleConfiguration.objects.count() == 0:
                self.stdout.write('  🔄 Inicializando sistema de módulos...')
                service = ModuleService()
                result = service.initialize_system()
                self.stdout.write(f'  ✅ Sistema inicializado: {result}')
            
            # Ativar módulos principais se estiverem inativos
            core_modules = ['accounts', 'config', 'pages']
            for module_name in core_modules:
                try:
                    module = AppModuleConfiguration.objects.get(app_name=module_name)
                    if not module.is_enabled or module.status != 'active':
                        module.is_enabled = True
                        module.status = 'active'
                        module.save()
                        self.stdout.write(f'  ✅ Módulo {module_name} ativado')
                except AppModuleConfiguration.DoesNotExist:
                    self.stdout.write(f'  ⚠️  Módulo {module_name} não encontrado')
            
        except Exception as e:
            self.stdout.write(f'  ❌ Erro ao corrigir problemas: {e}')
