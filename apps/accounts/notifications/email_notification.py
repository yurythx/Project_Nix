from apps.accounts.interfaces.notifications import INotificationService
from apps.accounts.services.email_service import EmailService
import logging

logger = logging.getLogger(__name__)


class EmailNotificationService(INotificationService):
    """Serviço de notificação por e-mail com configurações dinâmicas"""

    def __init__(self):
        self.email_service = EmailService()

    def send_registration_confirmation(self, email: str, code: str) -> None:
        """Envia e-mail de confirmação de registro"""
        try:
            success = self.email_service.send_registration_confirmation(email, code)

            if not success:
                raise Exception('Falha ao enviar email de confirmação')

        except Exception as e:
            logger.error(f'Erro ao enviar email de confirmação para {email}: {str(e)}', exc_info=True)
            raise Exception(f'Erro ao enviar email de verificação: {str(e)}')

    def send_password_reset_code(self, email: str, code: str) -> None:
        """Envia e-mail com código para reset de senha"""
        try:
            success = self.email_service.send_password_reset_code(email, code)

            if not success:
                raise Exception('Falha ao enviar código de redefinição')

        except Exception as e:
            logger.error(f'Erro ao enviar código de redefinição para {email}: {str(e)}', exc_info=True)
            raise Exception(f'Erro ao enviar código de redefinição: {str(e)}')
    
    def send_email_change_confirmation(self, email: str, code: str) -> None:
        """Envia e-mail de confirmação de alteração de e-mail"""
        try:
            context = {
                'email': email,
                'code': code,
                'site_name': 'HAVOC'
            }

            success = self.email_service.send_template_email(
                template_name='accounts/emails/email_change.html',
                context=context,
                subject='🔄 Confirmação de Alteração de E-mail - HAVOC',
                recipient_list=[email],
                fail_silently=False
            )

            if not success:
                raise Exception('Falha ao enviar email de confirmação de alteração')

        except Exception as e:
            logger.error(f'Erro ao enviar confirmação de alteração para {email}: {str(e)}', exc_info=True)
            raise Exception(f'Erro ao enviar email de confirmação: {str(e)}')