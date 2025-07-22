from apps.accounts.interfaces.services import IRegistrationService
from apps.accounts.interfaces.repositories import IUserRepository, IVerificationRepository
from apps.accounts.interfaces.notifications import INotificationService
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.contrib.auth import get_user_model
import logging
from core.observers import event_dispatcher
from typing import Dict, Any

User = get_user_model()
logger = logging.getLogger(__name__)

# Import local para evitar circular import
def get_verification_code_model():
    from apps.accounts.models.verification import VerificationCode
    return VerificationCode

class RegistrationService(IRegistrationService):
    """Serviço para gerenciamento de registro de usuários"""

    def __init__(
        self,
        user_repository: IUserRepository,
        verification_repository: IVerificationRepository,
        notification_service: INotificationService
    ):
        self.user_repository = user_repository
        self.verification_repository = verification_repository
        self.notification_service = notification_service

    @transaction.atomic
    def register_user(self, email: str, password: str, **extra_fields) -> User:
        """
        Registra um novo usuário
        :raises ValueError: Se o usuário já existir
        """
        logger.info(f"Iniciando registro para o email: {email}")
        # Centralizar regras de negócio aqui:
        if self.user_repository.exists_by_email(email):
            raise ValueError("Já existe um usuário com este e-mail.")
        if 'username' in extra_fields and self.user_repository.exists_by_username(extra_fields['username']):
            raise ValueError("Já existe um usuário com este nome de usuário.")
        # Cria usuário não verificado
        user = self.user_repository.create_user(
            email=email,
            password=password,
            is_verified=False,
            **extra_fields
        )
        # Gera e envia código de verificação
        VerificationCode = get_verification_code_model()
        code = self.verification_repository.create_verification_code(
            user=user,
            code_type=VerificationCode.REGISTRATION
        )
        self.notification_service.send_registration_confirmation(email, code)
        
        # Dispara evento para observers
        from core.observers import Event
        from datetime import datetime
        event = Event(
            name='user_registered',
            data={
                'user': user,
                'verification': code
            },
            timestamp=datetime.now(),
            source='registration_service'
        )
        event_dispatcher.dispatch(event)
        
        return user
    
    def confirm_registration(self, email: str, code: str) -> bool:
        """
        Confirma o registro de um usuário
        :return: True se a confirmação for bem-sucedida
        """
        user = self.user_repository.get_user_by_email(email)

        # Se já estiver verificado, retorna True
        if user.is_verified:
            return True

        # Verifica o código
        VerificationCode = get_verification_code_model()
        is_valid = self.verification_repository.verify_code(
            user=user,
            code=code,
            code_type=VerificationCode.REGISTRATION
        )

        if is_valid:
            # Atualiza usuário como verificado
            self.user_repository.update_user(user, is_verified=True)
            # Remove o código usado
            self.verification_repository.delete_code(user, VerificationCode.REGISTRATION)
            return True

        return False

    def resend_verification_code(self, email: str) -> bool:
        """
        Reenvia o código de verificação de registro para o email informado.
        :return: True se o código foi reenviado com sucesso
        """
        try:
            user = self.user_repository.get_user_by_email(email)
            if user.is_verified:
                logger.info(f"Usuário {email} já está verificado, não é necessário reenviar código.")
                return False
            VerificationCode = get_verification_code_model()
            # Remove códigos antigos
            self.verification_repository.delete_code(user, VerificationCode.REGISTRATION)
            # Gera novo código
            code = self.verification_repository.create_verification_code(
                user=user,
                code_type=VerificationCode.REGISTRATION
            )
            self.notification_service.send_registration_confirmation(email, code)
            logger.info(f"Código de verificação reenviado para: {email}")
            return True
        except ObjectDoesNotExist:
            logger.warning(f"Tentativa de reenviar código para email não cadastrado: {email}")
            return False
        except Exception as e:
            logger.error(f"Erro ao reenviar código de verificação: {str(e)}")
            return False

    def verify_registration(self, email: str, code: str) -> bool:
        """
        Verifica o código de registro do usuário e ativa a conta se válido.
        :return: True se a verificação for bem-sucedida
        """
        try:
            user = self.user_repository.get_user_by_email(email)
            if user.is_verified:
                return True
            VerificationCode = get_verification_code_model()
            is_valid = self.verification_repository.verify_code(
                user=user,
                code=code,
                code_type=VerificationCode.REGISTRATION
            )
            if is_valid:
                self.user_repository.update_user(user, is_verified=True)
                self.verification_repository.delete_code(user, VerificationCode.REGISTRATION)
                logger.info(f"Usuário {email} verificado com sucesso.")
                return True
            logger.warning(f"Código de verificação inválido para {email}.")
            return False
        except ObjectDoesNotExist:
            logger.warning(f"Tentativa de verificar registro para email não cadastrado: {email}")
            return False
        except Exception as e:
            logger.error(f"Erro ao verificar registro: {str(e)}")
            return False