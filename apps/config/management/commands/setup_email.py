"""
Comando para configurar email rapidamente via linha de comando.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.config.services.email_config_service import DynamicEmailConfigService
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Configura email rapidamente via linha de comando'

    def add_arguments(self, parser):
        parser.add_argument(
            '--backend',
            type=str,
            choices=['smtp', 'console', 'file', 'dummy'],
            default='console',
            help='Backend de email (smtp, console, file, dummy)',
        )
        parser.add_argument(
            '--host',
            type=str,
            help='Servidor SMTP (ex: smtp.gmail.com)',
        )
        parser.add_argument(
            '--port',
            type=int,
            default=587,
            help='Porta SMTP (padrão: 587)',
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Usuário SMTP',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Senha SMTP',
        )
        parser.add_argument(
            '--from-email',
            type=str,
            help='Email padrão de envio',
        )
        parser.add_argument(
            '--tls',
            action='store_true',
            help='Usar TLS',
        )
        parser.add_argument(
            '--ssl',
            action='store_true',
            help='Usar SSL',
        )
        parser.add_argument(
            '--admin-user',
            type=str,
            help='Username do admin para salvar a configuração',
        )

    def handle(self, *args, **options):
        try:
            self.stdout.write('📧 Configuração Rápida de Email')
            self.stdout.write('=' * 40)
            
            # Determinar backend
            backend_choice = options['backend']
            backend_mapping = {
                'smtp': 'django.core.mail.backends.smtp.EmailBackend',
                'console': 'django.core.mail.backends.console.EmailBackend',
                'file': 'django.core.mail.backends.filebased.EmailBackend',
                'dummy': 'django.core.mail.backends.dummy.EmailBackend',
            }
            
            email_backend = backend_mapping[backend_choice]
            
            # Configuração base
            email_config = {
                'EMAIL_BACKEND': email_backend,
                'EMAIL_HOST': options.get('host', ''),
                'EMAIL_PORT': options.get('port', 587),
                'EMAIL_HOST_USER': options.get('user', ''),
                'EMAIL_HOST_PASSWORD': options.get('password', ''),
                'EMAIL_USE_TLS': options.get('tls', True),
                'EMAIL_USE_SSL': options.get('ssl', False),
                'DEFAULT_FROM_EMAIL': options.get('from_email', 'noreply@fireflies.com'),
                'EMAIL_TIMEOUT': 30,
            }
            
            # Configurações específicas por backend
            if backend_choice == 'console':
                email_config.update({
                    'EMAIL_HOST': '',
                    'EMAIL_HOST_USER': '',
                    'EMAIL_HOST_PASSWORD': '',
                    'DEFAULT_FROM_EMAIL': 'noreply@localhost',
                })
            elif backend_choice == 'file':
                email_config.update({
                    'EMAIL_FILE_PATH': '/tmp/django-mails',
                    'EMAIL_HOST': '',
                    'EMAIL_HOST_USER': '',
                    'EMAIL_HOST_PASSWORD': '',
                    'DEFAULT_FROM_EMAIL': 'noreply@localhost',
                })
            elif backend_choice == 'dummy':
                email_config.update({
                    'EMAIL_HOST': '',
                    'EMAIL_HOST_USER': '',
                    'EMAIL_HOST_PASSWORD': '',
                    'DEFAULT_FROM_EMAIL': 'noreply@localhost',
                })
            
            # Mostrar configuração
            self.stdout.write(f'\n🔧 Configuração a ser aplicada:')
            self.stdout.write('-' * 30)
            for key, value in email_config.items():
                if key == 'EMAIL_HOST_PASSWORD':
                    self.stdout.write(f'  {key}: {"*" * len(str(value)) if value else "não definida"}')
                else:
                    self.stdout.write(f'  {key}: {value}')
            
            # Confirmar
            if not self.confirm_configuration():
                self.stdout.write('❌ Configuração cancelada')
                return
            
            # Obter usuário admin
            admin_user = None
            if options.get('admin_user'):
                try:
                    admin_user = User.objects.get(username=options['admin_user'])
                except User.DoesNotExist:
                    self.stdout.write(f'⚠️ Usuário {options["admin_user"]} não encontrado')
            
            if not admin_user:
                admin_user = User.objects.filter(is_superuser=True).first()
                if admin_user:
                    self.stdout.write(f'👤 Usando admin: {admin_user.username}')
                else:
                    self.stdout.write('⚠️ Nenhum superusuário encontrado')
            
            # Salvar configuração
            self.stdout.write('\n💾 Salvando configuração...')
            email_service = DynamicEmailConfigService()
            
            success = email_service.save_config(
                config_dict=email_config,
                user=admin_user,
                description=f'Configuração via comando - Backend: {backend_choice}'
            )
            
            if success:
                self.stdout.write('✅ Configuração salva com sucesso!')
                
                # Testar conexão
                self.stdout.write('\n🔗 Testando conexão...')
                connection_success, message = email_service.test_connection()
                if connection_success:
                    self.stdout.write(f'✅ {message}')
                else:
                    self.stdout.write(f'⚠️ {message}')
                
                # Sincronizar com .env
                self.stdout.write('\n🔄 Sincronizando com arquivo .env...')
                sync_success = email_service.sync_config_to_env()
                if sync_success:
                    self.stdout.write('✅ Configuração sincronizada com .env')
                else:
                    self.stdout.write('⚠️ Erro ao sincronizar com .env')
                
                self.stdout.write('\n🎉 Configuração concluída!')
                self.stdout.write('💡 Para aplicar completamente, reinicie o servidor Django.')
                
            else:
                self.stdout.write('❌ Erro ao salvar configuração')
                
        except Exception as e:
            logger.error(f'Erro ao configurar email: {e}', exc_info=True)
            self.stdout.write(f'❌ Erro inesperado: {str(e)}')
    
    def confirm_configuration(self):
        """Confirma se o usuário quer aplicar a configuração"""
        while True:
            response = input('\n❓ Aplicar esta configuração? (s/n): ').lower().strip()
            if response in ['s', 'sim', 'y', 'yes']:
                return True
            elif response in ['n', 'não', 'no']:
                return False
            else:
                self.stdout.write('Por favor, responda com s/n') 