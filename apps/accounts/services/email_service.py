from django.core.mail import send_mail, get_connection
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from apps.accounts.interfaces.services import IEmailService
import logging
import smtplib

logger = logging.getLogger(__name__)


class EmailService(IEmailService):
    """
    Serviço avançado para envio de emails com configurações dinâmicas
    """
    
    def __init__(self):
        self.config = self._load_email_config()
    
    def _load_email_config(self):
        """Carrega configurações de email do sistema"""
        try:
            # Primeiro, tentar carregar da configuração padrão no banco
            from apps.config.models import EmailConfiguration

            default_config = EmailConfiguration.get_default()
            if default_config and default_config.is_active:
                return default_config.get_config_dict()

            # Se não há configuração padrão, tentar carregar do sistema antigo
            from apps.config.services.system_config_service import SystemConfigService
            from apps.config.repositories.config_repository import DjangoSystemConfigRepository

            config_service = SystemConfigService(
                DjangoSystemConfigRepository(),
                None
            )

            email_config = config_service.get_config('email_settings')

            if email_config and isinstance(email_config, dict):
                return email_config

        except Exception as e:
            logger.warning(f'Não foi possível carregar configurações de email: {e}')

        # Fallback para configurações do Django
        return {
            'EMAIL_BACKEND': getattr(settings, 'EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend'),
            'EMAIL_HOST': getattr(settings, 'EMAIL_HOST', ''),
            'EMAIL_PORT': getattr(settings, 'EMAIL_PORT', 587),
            'EMAIL_HOST_USER': getattr(settings, 'EMAIL_HOST_USER', ''),
            'EMAIL_HOST_PASSWORD': getattr(settings, 'EMAIL_HOST_PASSWORD', ''),
            'EMAIL_USE_TLS': getattr(settings, 'EMAIL_USE_TLS', True),
            'EMAIL_USE_SSL': getattr(settings, 'EMAIL_USE_SSL', False),
            'DEFAULT_FROM_EMAIL': getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@havoc.com'),
            'EMAIL_TIMEOUT': getattr(settings, 'EMAIL_TIMEOUT', 30),
        }
    
    def get_connection(self):
        """Cria conexão de email com configurações dinâmicas"""
        if self.config['EMAIL_BACKEND'] == 'django.core.mail.backends.smtp.EmailBackend':
            return get_connection(
                backend=self.config['EMAIL_BACKEND'],
                host=self.config['EMAIL_HOST'],
                port=self.config['EMAIL_PORT'],
                username=self.config['EMAIL_HOST_USER'],
                password=self.config['EMAIL_HOST_PASSWORD'],
                use_tls=self.config['EMAIL_USE_TLS'],
                use_ssl=self.config['EMAIL_USE_SSL'],
                timeout=self.config['EMAIL_TIMEOUT'],
                fail_silently=False
            )
        else:
            return get_connection(backend=self.config['EMAIL_BACKEND'])
    
    def test_connection(self):
        """Testa a conexão SMTP"""
        try:
            if self.config['EMAIL_BACKEND'] != 'django.core.mail.backends.smtp.EmailBackend':
                return True, f"Backend {self.config['EMAIL_BACKEND']} não requer teste de conexão"
            
            connection = self.get_connection()
            connection.open()
            connection.close()
            
            return True, "Conexão SMTP estabelecida com sucesso!"
            
        except smtplib.SMTPAuthenticationError:
            return False, "Erro de autenticação: Verifique usuário e senha"
        except smtplib.SMTPConnectError:
            return False, f"Erro de conexão: Não foi possível conectar ao servidor {self.config['EMAIL_HOST']}:{self.config['EMAIL_PORT']}"
        except smtplib.SMTPServerDisconnected:
            return False, "Servidor SMTP desconectou inesperadamente"
        except Exception as e:
            return False, f"Erro na conexão SMTP: {str(e)}"
    
    def send_email(self, subject, message, recipient_list, html_message=None, fail_silently=False):
        """Envia email usando configurações dinâmicas"""
        try:
            connection = self.get_connection()
            
            return send_mail(
                subject=subject,
                message=message,
                from_email=self.config['DEFAULT_FROM_EMAIL'],
                recipient_list=recipient_list,
                html_message=html_message,
                connection=connection,
                fail_silently=fail_silently
            )
            
        except Exception as e:
            logger.error(f'Erro ao enviar email: {e}', exc_info=True)
            if not fail_silently:
                raise
            return False
    
    def send_template_email(self, template_name, context, subject, recipient_list, fail_silently=False):
        """Envia email usando template"""
        try:
            html_message = render_to_string(template_name, context)
            plain_message = strip_tags(html_message)
            
            return self.send_email(
                subject=subject,
                message=plain_message,
                recipient_list=recipient_list,
                html_message=html_message,
                fail_silently=fail_silently
            )
            
        except Exception as e:
            logger.error(f'Erro ao enviar email com template: {e}', exc_info=True)
            if not fail_silently:
                raise
            return False
    
    def send_password_reset_code(self, email, code):
        """Envia código de redefinição de senha"""
        try:
            context = {
                'email': email,
                'code': code,
                'site_name': 'HAVOC',
                'timeout_minutes': 15
            }
            
            success = self.send_template_email(
                template_name='accounts/emails/password_reset.html',
                context=context,
                subject='🔒 Código para Redefinição de Senha - HAVOC',
                recipient_list=[email],
                fail_silently=False
            )
            
            if success:
                logger.info(f'Código de redefinição de senha enviado para: {email}')
                return True
            else:
                logger.error(f'Falha ao enviar código de redefinição para: {email}')
                return False
                
        except Exception as e:
            logger.error(f'Erro ao enviar código de redefinição para {email}: {e}', exc_info=True)
            raise Exception(f'Erro ao enviar email de redefinição: {str(e)}')
    
    def send_registration_confirmation(self, email, code):
        """Envia código de confirmação de registro"""
        try:
            context = {
                'email': email,
                'code': code,
                'site_name': 'HAVOC'
            }
            
            success = self.send_template_email(
                template_name='accounts/emails/registration_confirmation.html',
                context=context,
                subject='✅ Confirmação de Cadastro - HAVOC',
                recipient_list=[email],
                fail_silently=False
            )
            
            if success:
                logger.info(f'Email de confirmação enviado para: {email}')
                return True
            else:
                logger.error(f'Falha ao enviar confirmação para: {email}')
                return False
                
        except Exception as e:
            logger.error(f'Erro ao enviar confirmação para {email}: {e}', exc_info=True)
            raise Exception(f'Erro ao enviar email de confirmação: {str(e)}')
    
    def send_test_email(self, recipient_email, user_name=None):
        """Envia email de teste"""
        try:
            from datetime import datetime
            
            context = {
                'user_name': user_name or 'Usuário',
                'test_time': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                'site_name': 'HAVOC',
                'email_config': {
                    'backend': self.config.get('EMAIL_BACKEND', 'Desconhecido'),
                    'host': self.config.get('EMAIL_HOST', 'Não configurado'),
                    'port': self.config.get('EMAIL_PORT', 'Não configurado'),
                    'use_tls': self.config.get('EMAIL_USE_TLS', False),
                    'use_ssl': self.config.get('EMAIL_USE_SSL', False),
                }
            }
            
            success = self.send_template_email(
                template_name='accounts/email_diagnostic.html',
                context=context,
                subject='🧪 Teste de Configuração de Email - HAVOC',
                recipient_list=[recipient_email],
                fail_silently=False
            )
            
            if success:
                logger.info(f'Email de teste enviado para: {recipient_email}')
                return True
            else:
                logger.error(f'Falha ao enviar email de teste para: {recipient_email}')
                return False
                
        except Exception as e:
            logger.error(f'Erro ao enviar email de teste para {recipient_email}: {e}', exc_info=True)
            raise Exception(f'Erro ao enviar email de teste: {str(e)}')
    
    def get_config_status(self):
        """Retorna status da configuração de email"""
        try:
            # Testar conexão
            connection_success, connection_message = self.test_connection()
            
            return {
                'config_loaded': bool(self.config),
                'backend': self.config.get('EMAIL_BACKEND', 'Desconhecido'),
                'host': self.config.get('EMAIL_HOST', 'Não configurado'),
                'port': self.config.get('EMAIL_PORT', 'Não configurado'),
                'use_tls': self.config.get('EMAIL_USE_TLS', False),
                'use_ssl': self.config.get('EMAIL_USE_SSL', False),
                'connection_test': {
                    'success': connection_success,
                    'message': connection_message
                },
                'from_email': self.config.get('DEFAULT_FROM_EMAIL', 'Não configurado'),
                'timeout': self.config.get('EMAIL_TIMEOUT', 30),
            }
            
        except Exception as e:
            logger.error(f'Erro ao obter status da configuração: {e}')
            return {
                'config_loaded': False,
                'error': str(e),
                'connection_test': {
                    'success': False,
                    'message': f'Erro ao testar configuração: {str(e)}'
                }
            }
