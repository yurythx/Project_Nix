"""
Comando para verificar o status das configurações de email.
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from apps.config.services.email_config_service import DynamicEmailConfigService
from apps.config.repositories.config_repository import DjangoSystemConfigRepository
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Verifica o status das configurações de email'

    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Mostra informações detalhadas',
        )
        parser.add_argument(
            '--test-connection',
            action='store_true',
            help='Testa a conexão de email',
        )

    def handle(self, *args, **options):
        try:
            self.stdout.write('📧 Verificando Configurações de Email')
            self.stdout.write('=' * 50)
            
            # 1. Verificar configurações do settings.py
            self.stdout.write('\n🔧 Configurações do Settings.py:')
            self.stdout.write('-' * 30)
            settings_config = {
                'EMAIL_BACKEND': getattr(settings, 'EMAIL_BACKEND', 'Não definido'),
                'EMAIL_HOST': getattr(settings, 'EMAIL_HOST', 'Não definido'),
                'EMAIL_PORT': getattr(settings, 'EMAIL_PORT', 'Não definido'),
                'EMAIL_HOST_USER': getattr(settings, 'EMAIL_HOST_USER', 'Não definido'),
                'EMAIL_USE_TLS': getattr(settings, 'EMAIL_USE_TLS', 'Não definido'),
                'EMAIL_USE_SSL': getattr(settings, 'EMAIL_USE_SSL', 'Não definido'),
                'DEFAULT_FROM_EMAIL': getattr(settings, 'DEFAULT_FROM_EMAIL', 'Não definido'),
            }
            
            for key, value in settings_config.items():
                if key == 'EMAIL_HOST_PASSWORD':
                    self.stdout.write(f'  {key}: {"*" * 8 if value else "Não definido"}')
                else:
                    self.stdout.write(f'  {key}: {value}')
            
            # 2. Verificar configurações do banco de dados
            self.stdout.write('\n💾 Configurações do Banco de Dados:')
            self.stdout.write('-' * 30)
            try:
                repo = DjangoSystemConfigRepository()
                db_config = repo.get_by_key('email_settings')
                if db_config:
                    self.stdout.write(self.style.SUCCESS('✅ Configuração encontrada no banco'))
                    if options['detailed']:
                        for key, value in db_config.items():
                            if key == 'EMAIL_HOST_PASSWORD':
                                self.stdout.write(f'  {key}: {"*" * len(str(value)) if value else "Não definida"}')
                            else:
                                self.stdout.write(f'  {key}: {value}')
                else:
                    self.stdout.write(self.style.WARNING('⚠️ Nenhuma configuração encontrada no banco'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Erro ao acessar banco: {e}'))
            
            # 3. Verificar configuração ativa (via serviço)
            self.stdout.write('\n🎯 Configuração Ativa (Serviço):')
            self.stdout.write('-' * 30)
            try:
                email_service = DynamicEmailConfigService()
                active_config = email_service.get_active_config()
                
                if active_config:
                    # Verificar se está configurado
                    is_configured = bool(
                        active_config.get('EMAIL_HOST') and 
                        active_config.get('EMAIL_HOST_USER') and
                        active_config.get('EMAIL_BACKEND') != 'django.core.mail.backends.dummy.EmailBackend'
                    )
                    
                    if is_configured:
                        self.stdout.write(self.style.SUCCESS('✅ Email configurado e ativo'))
                    else:
                        self.stdout.write(self.style.WARNING('⚠️ Email não configurado completamente'))
                    
                    if options['detailed']:
                        for key, value in active_config.items():
                            if key == 'EMAIL_HOST_PASSWORD':
                                self.stdout.write(f'  {key}: {"*" * len(str(value)) if value else "Não definida"}')
                            else:
                                self.stdout.write(f'  {key}: {value}')
                else:
                    self.stdout.write(self.style.ERROR('❌ Nenhuma configuração ativa encontrada'))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Erro ao verificar configuração ativa: {e}'))
            
            # 4. Testar conexão se solicitado
            if options['test_connection']:
                self.stdout.write('\n🔗 Testando Conexão:')
                self.stdout.write('-' * 30)
                try:
                    success, message = email_service.test_connection()
                    if success:
                        self.stdout.write(self.style.SUCCESS(f'✅ {message}'))
                    else:
                        self.stdout.write(self.style.ERROR(f'❌ {message}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'❌ Erro ao testar conexão: {e}'))
            
            # 5. Resumo
            self.stdout.write('\n📋 Resumo:')
            self.stdout.write('-' * 30)
            
            # Verificar se há configuração válida
            has_valid_config = bool(
                active_config and
                active_config.get('EMAIL_HOST') and 
                active_config.get('EMAIL_HOST_USER') and
                active_config.get('EMAIL_BACKEND') != 'django.core.mail.backends.dummy.EmailBackend'
            )
            
            if has_valid_config:
                self.stdout.write(self.style.SUCCESS('✅ Sistema de email configurado e pronto para uso'))
                self.stdout.write(f'   Servidor: {active_config.get("EMAIL_HOST")}')
                self.stdout.write(f'   Usuário: {active_config.get("EMAIL_HOST_USER")}')
                self.stdout.write(f'   Backend: {active_config.get("EMAIL_BACKEND")}')
            else:
                self.stdout.write(self.style.WARNING('⚠️ Sistema de email não configurado'))
                self.stdout.write('   Execute: python manage.py setup_email para configurar')
            
            # 6. Comandos úteis
            self.stdout.write('\n🛠️ Comandos Úteis:')
            self.stdout.write('-' * 30)
            self.stdout.write('  python manage.py check_email_config --detailed')
            self.stdout.write('  python manage.py check_email_config --test-connection')
            self.stdout.write('  python manage.py setup_email')
            self.stdout.write('  python manage.py sync_email_config')

        except Exception as e:
            logger.error(f'Erro ao verificar configurações de email: {e}', exc_info=True)
            self.stdout.write(self.style.ERROR(f'❌ Erro inesperado: {str(e)}')) 