from abc import ABC, abstractmethod

class INotificationService(ABC):
    """Interface para serviços de notificação"""
    
    @abstractmethod
    def send_registration_confirmation(self, email: str, code: str) -> None:
        """
        Envia código de confirmação de registro por email
        :param email: Email do destinatário
        :param code: Código de verificação
        """
        pass
    
    @abstractmethod
    def send_password_reset_code(self, email: str, code: str) -> None:
        """
        Envia código de reset de senha por email
        :param email: Email do destinatário
        :param code: Código de verificação
        """
        pass
    
    @abstractmethod
    def send_email_change_confirmation(self, email: str, code: str) -> None:
        """
        Envia código de confirmação de alteração de email
        :param email: Novo email do usuário
        :param code: Código de verificação
        """
        pass