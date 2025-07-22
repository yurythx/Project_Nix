from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.test.utils import get_runner
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import Client
from apps.config.models import AppModuleConfiguration
from apps.config.services.module_service import ModuleService
import sys
import io

User = get_user_model()


class Command(BaseCommand):
    help = 'Executa verificação completa de saúde do sistema'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-tests',
            action='store_true',
            help='Pula execução de testes unitários',
        )
        parser.add_argument(
            '--quick',
            action='store_true',
            help='Execução rápida (apenas verificações básicas)',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🏥 VERIFICAÇÃO DE SAÚDE DO SISTEMA HAVOC')
        )
        self.stdout.write('=' * 60)
        
        skip_tests = options.get('skip_tests', False)
        quick_mode = options.get('quick', False)
        
        # Contadores
        total_checks = 0
        passed_checks = 0
        failed_checks = 0
        
        # 1. Verificações básicas do Django
        self.stdout.write('\n📋 1. VERIFICAÇÕES BÁSICAS DO DJANGO')
        self.stdout.write('-' * 40)
        
        checks = [
            ('Configurações Django', self._check_django_settings),
            ('Banco de Dados', self._check_database),
            ('Migrações', self._check_migrations),
            ('Arquivos Estáticos', self._check_static_files),
            ('URLs Principais', self._check_main_urls),
        ]
        
        for check_name, check_func in checks:
            total_checks += 1
            if self._run_check(check_name, check_func):
                passed_checks += 1
            else:
                failed_checks += 1
        
        # 2. Verificações dos Apps
        self.stdout.write('\n📱 2. VERIFICAÇÕES DOS APPS')
        self.stdout.write('-' * 40)
        
        app_checks = [
            ('App Accounts', self._check_accounts_app),
            ('App Pages', self._check_pages_app),
            ('App Articles', self._check_articles_app),
            ('App Config', self._check_config_app),
        ]
        
        for check_name, check_func in app_checks:
            total_checks += 1
            if self._run_check(check_name, check_func):
                passed_checks += 1
            else:
                failed_checks += 1
        
        # 3. Sistema de Módulos
        self.stdout.write('\n🧩 3. SISTEMA DE MÓDULOS')
        self.stdout.write('-' * 40)
        
        module_checks = [
            ('Configuração de Módulos', self._check_module_system),
            ('Middleware de Módulos', self._check_module_middleware),
            ('Estatísticas de Módulos', self._check_module_stats),
        ]
        
        for check_name, check_func in module_checks:
            total_checks += 1
            if self._run_check(check_name, check_func):
                passed_checks += 1
            else:
                failed_checks += 1
        
        # 4. Testes Unitários (se não pulados)
        if not skip_tests and not quick_mode:
            self.stdout.write('\n🧪 4. TESTES UNITÁRIOS')
            self.stdout.write('-' * 40)
            
            total_checks += 1
            if self._run_check('Testes Unitários', self._run_unit_tests):
                passed_checks += 1
            else:
                failed_checks += 1
        
        # 5. Verificações de Segurança
        if not quick_mode:
            self.stdout.write('\n🔒 5. VERIFICAÇÕES DE SEGURANÇA')
            self.stdout.write('-' * 40)
            
            security_checks = [
                ('Configurações de Segurança', self._check_security_settings),
                ('Middleware de Segurança', self._check_security_middleware),
                ('Autenticação', self._check_authentication),
            ]
            
            for check_name, check_func in security_checks:
                total_checks += 1
                if self._run_check(check_name, check_func):
                    passed_checks += 1
                else:
                    failed_checks += 1
        
        # Resumo Final
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('📊 RESUMO DA VERIFICAÇÃO')
        self.stdout.write('=' * 60)
        
        success_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        
        self.stdout.write(f'✅ Verificações Aprovadas: {passed_checks}')
        self.stdout.write(f'❌ Verificações Falharam: {failed_checks}')
        self.stdout.write(f'📈 Taxa de Sucesso: {success_rate:.1f}%')
        
        if failed_checks == 0:
            self.stdout.write(
                self.style.SUCCESS('\n🎉 SISTEMA TOTALMENTE SAUDÁVEL!')
            )
        elif failed_checks <= 2:
            self.stdout.write(
                self.style.WARNING('\n⚠️  Sistema com pequenos problemas')
            )
        else:
            self.stdout.write(
                self.style.ERROR('\n🚨 Sistema com problemas críticos')
            )
        
        # Retorna código de saída
        if failed_checks == 0:
            sys.exit(0)  # Sucesso
        else:
            sys.exit(1)  # Falha
    
    def _run_check(self, check_name, check_func):
        """Executa uma verificação individual"""
        try:
            result = check_func()
            if result:
                self.stdout.write(f'  ✅ {check_name}')
                return True
            else:
                self.stdout.write(f'  ❌ {check_name}')
                return False
        except Exception as e:
            self.stdout.write(f'  ❌ {check_name} - Erro: {str(e)}')
            return False
    
    def _check_django_settings(self):
        """Verifica configurações básicas do Django"""
        try:
            # Verifica se DEBUG está configurado
            debug_ok = hasattr(settings, 'DEBUG')
            
            # Verifica se SECRET_KEY existe
            secret_key_ok = hasattr(settings, 'SECRET_KEY') and settings.SECRET_KEY
            
            # Verifica INSTALLED_APPS
            apps_ok = hasattr(settings, 'INSTALLED_APPS') and len(settings.INSTALLED_APPS) > 0
            
            return debug_ok and secret_key_ok and apps_ok
        except Exception:
            return False
    
    def _check_database(self):
        """Verifica conexão com banco de dados"""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except Exception:
            return False
    
    def _check_migrations(self):
        """Verifica se há migrações pendentes"""
        try:
            # Captura output do comando
            output = io.StringIO()
            call_command('showmigrations', '--plan', stdout=output)
            migrations_output = output.getvalue()
            
            # Se não há migrações não aplicadas, não deve ter [ ] no output
            return '[ ]' not in migrations_output
        except Exception:
            return False
    
    def _check_static_files(self):
        """Verifica configuração de arquivos estáticos"""
        try:
            static_url_ok = hasattr(settings, 'STATIC_URL') and settings.STATIC_URL
            static_root_ok = hasattr(settings, 'STATIC_ROOT')
            return static_url_ok and static_root_ok
        except Exception:
            return False
    
    def _check_main_urls(self):
        """Verifica URLs principais"""
        try:
            client = Client()
            
            # Testa URLs principais
            urls_to_test = ['/', '/sobre/', '/contato/', '/artigos/']
            
            for url in urls_to_test:
                response = client.get(url)
                if response.status_code not in [200, 302]:
                    return False
            
            return True
        except Exception:
            return False
    
    def _check_accounts_app(self):
        """Verifica app accounts"""
        try:
            # Verifica se o modelo User existe
            User.objects.count()
            
            # Verifica URLs básicas
            client = Client()
            response = client.get('/accounts/login/')
            return response.status_code in [200, 302]
        except Exception:
            return False
    
    def _check_pages_app(self):
        """Verifica app pages"""
        try:
            from apps.pages.models import Page
            Page.objects.count()
            return True
        except Exception:
            return False
    
    def _check_articles_app(self):
        """Verifica app articles"""
        try:
            from apps.articles.models import Article, Category
            Article.objects.count()
            Category.objects.count()
            return True
        except Exception:
            return False
    
    def _check_config_app(self):
        """Verifica app config"""
        try:
            AppModuleConfiguration.objects.count()
            return True
        except Exception:
            return False
    
    def _check_module_system(self):
        """Verifica sistema de módulos"""
        try:
            module_service = ModuleService()
            modules = module_service.get_all_modules()
            return len(modules) > 0
        except Exception:
            return False
    
    def _check_module_middleware(self):
        """Verifica middleware de módulos"""
        try:
            middleware_classes = getattr(settings, 'MIDDLEWARE', [])
            return 'apps.config.middleware.module_middleware.ModuleAccessMiddleware' in middleware_classes
        except Exception:
            return False
    
    def _check_module_stats(self):
        """Verifica estatísticas de módulos"""
        try:
            module_service = ModuleService()
            stats = module_service.get_module_statistics()
            return 'total' in stats and 'enabled' in stats
        except Exception:
            return False
    
    def _run_unit_tests(self):
        """Executa testes unitários básicos"""
        try:
            # Executa apenas alguns testes básicos para não demorar muito
            output = io.StringIO()
            call_command('test', 'apps.accounts.tests.UserModelTest.test_create_user', 
                        verbosity=0, stdout=output, stderr=output)
            return True
        except Exception:
            return False
    
    def _check_security_settings(self):
        """Verifica configurações de segurança"""
        try:
            # Verifica algumas configurações básicas de segurança
            csrf_ok = 'django.middleware.csrf.CsrfViewMiddleware' in getattr(settings, 'MIDDLEWARE', [])
            session_ok = 'django.contrib.sessions.middleware.SessionMiddleware' in getattr(settings, 'MIDDLEWARE', [])
            auth_ok = 'django.contrib.auth.middleware.AuthenticationMiddleware' in getattr(settings, 'MIDDLEWARE', [])
            
            return csrf_ok and session_ok and auth_ok
        except Exception:
            return False
    
    def _check_security_middleware(self):
        """Verifica middleware de segurança"""
        try:
            middleware_classes = getattr(settings, 'MIDDLEWARE', [])
            security_middleware = 'django.middleware.security.SecurityMiddleware'
            return security_middleware in middleware_classes
        except Exception:
            return False
    
    def _check_authentication(self):
        """Verifica sistema de autenticação"""
        try:
            # Verifica se AUTH_USER_MODEL está configurado
            auth_user_model = getattr(settings, 'AUTH_USER_MODEL', None)
            return auth_user_model == 'accounts.User'
        except Exception:
            return False
