from abc import ABC, abstractmethod
from typing import Optional, Any, List, Dict
from django.contrib.auth import get_user_model

User = get_user_model()

class IRegistrationService(ABC):
    """Interface para serviços de registro de usuários"""
    
    @abstractmethod
    def register_user(self, user_data: Dict[str, Any]) -> User:
        """
        Registra um novo usuário
        :param user_data: Dados do usuário
        :return: Usuário criado
        """
        pass
    
    @abstractmethod
    def verify_registration(self, email: str, code: str) -> bool:
        """
        Verifica o código de registro
        :param email: Email do usuário
        :param code: Código de verificação
        :return: True se verificado com sucesso
        """
        pass
    
    @abstractmethod
    def resend_verification_code(self, email: str) -> bool:
        """
        Reenvia código de verificação
        :param email: Email do usuário
        :return: True se enviado com sucesso
        """
        pass

class IPasswordService(ABC):
    """Interface para serviços de senha"""
    
    @abstractmethod
    def change_password(self, user: User, old_password: str, new_password: str) -> bool:
        """
        Altera a senha do usuário
        :param user: Usuário
        :param old_password: Senha atual
        :param new_password: Nova senha
        :return: True se alterado com sucesso
        """
        pass
    
    @abstractmethod
    def reset_password_request(self, email: str) -> bool:
        """
        Solicita redefinição de senha
        :param email: Email do usuário
        :return: True se solicitado com sucesso
        """
        pass
    
    @abstractmethod
    def reset_password_confirm(self, email: str, code: str, new_password: str) -> bool:
        """
        Confirma redefinição de senha
        :param email: Email do usuário
        :param code: Código de redefinição
        :param new_password: Nova senha
        :return: True se redefinido com sucesso
        """
        pass

class IAuthService(ABC):
    """Interface para serviços de autenticação"""
    
    @abstractmethod
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Autentica um usuário
        :param email: Email do usuário
        :param password: Senha
        :return: Usuário autenticado ou None
        """
        pass
    
    @abstractmethod
    def logout_user(self, user: User) -> bool:
        """
        Faz logout do usuário
        :param user: Usuário
        :return: True se logout realizado com sucesso
        """
        pass

class IProfileService(ABC):
    """Interface para serviços de perfil de usuário"""
    
    @abstractmethod
    def get_user_profile(self, user: User) -> Dict[str, Any]:
        """
        Obtém o perfil do usuário
        :param user: Usuário
        :return: Dados do perfil
        """
        pass
    
    @abstractmethod
    def update_user_profile(self, user: User, profile_data: Dict[str, Any]) -> bool:
        """
        Atualiza o perfil do usuário
        :param user: Usuário
        :param profile_data: Dados para atualização
        :return: True se atualizado com sucesso
        """
        pass
    
    @abstractmethod
    def update_avatar(self, user: User, avatar_file) -> bool:
        """
        Atualiza o avatar do usuário
        :param user: Usuário
        :param avatar_file: Arquivo do avatar
        :return: True se atualizado com sucesso
        """
        pass
    
    @abstractmethod
    def delete_avatar(self, user: User) -> bool:
        """
        Remove o avatar do usuário
        :param user: Usuário
        :return: True se removido com sucesso
        """
        pass

class IEmailService(ABC):
    """Interface para serviços de email"""
    
    @abstractmethod
    def get_connection(self) -> Any:
        """
        Cria conexão de email
        :return: Conexão de email
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> tuple[bool, str]:
        """
        Testa a conexão de email
        :return: Tupla (sucesso, mensagem)
        """
        pass
    
    @abstractmethod
    def send_email(self, subject: str, message: str, recipient_list: List[str], 
                   html_message: str = None, fail_silently: bool = False) -> bool:
        """
        Envia email
        :param subject: Assunto do email
        :param message: Mensagem do email
        :param recipient_list: Lista de destinatários
        :param html_message: Mensagem HTML (opcional)
        :param fail_silently: Se deve falhar silenciosamente
        :return: True se enviado com sucesso
        """
        pass
    
    @abstractmethod
    def send_template_email(self, template_name: str, context: Dict[str, Any], 
                           subject: str, recipient_list: List[str], 
                           fail_silently: bool = False) -> bool:
        """
        Envia email usando template
        :param template_name: Nome do template
        :param context: Contexto para o template
        :param subject: Assunto do email
        :param recipient_list: Lista de destinatários
        :param fail_silently: Se deve falhar silenciosamente
        :return: True se enviado com sucesso
        """
        pass
    
    @abstractmethod
    def send_password_reset_code(self, email: str, code: str) -> bool:
        """
        Envia código de redefinição de senha
        :param email: Email do usuário
        :param code: Código de redefinição
        :return: True se enviado com sucesso
        """
        pass
    
    @abstractmethod
    def send_registration_confirmation(self, email: str, code: str) -> bool:
        """
        Envia código de confirmação de registro
        :param email: Email do usuário
        :param code: Código de confirmação
        :return: True se enviado com sucesso
        """
        pass
    
    @abstractmethod
    def send_test_email(self, recipient_email: str, user_name: str = None) -> bool:
        """
        Envia email de teste
        :param recipient_email: Email do destinatário
        :param user_name: Nome do usuário (opcional)
        :return: True se enviado com sucesso
        """
        pass