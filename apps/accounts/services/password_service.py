from apps.accounts.interfaces.services import IPasswordService
from apps.accounts.interfaces.repositories import IUserRepository, IVerificationRepository
from apps.accounts.interfaces.notifications import INotificationService
from django.core.exceptions import ObjectDoesNotExist

# Import local para evitar circular import
def get_verification_code_model():
    from apps.accounts.models.verification import VerificationCode
    return VerificationCode

class PasswordService(IPasswordService):
    """Serviço para gerenciamento de senhas de usuários"""
    
    def __init__(
        self, 
        user_repository: IUserRepository,
        verification_repository: IVerificationRepository,
        notification_service: INotificationService
    ):
        self.user_repository = user_repository
        self.verification_repository = verification_repository
        self.notification_service = notification_service
    
    def request_password_reset(self, email: str) -> bool:
        """
        Solicita um reset de senha
        :return: True se a solicitação for válida
        """
        try:
            user = self.user_repository.get_user_by_email(email)
            
            if not user.is_verified:
                return False
                
            # Gera e envia código de verificação
            VerificationCode = get_verification_code_model()
            code = self.verification_repository.create_verification_code(
                user=user,
                code_type=VerificationCode.PASSWORD_RESET
            )
            
            self.notification_service.send_password_reset_code(email, code)
            return True
        except ObjectDoesNotExist:
            return False
    
    def confirm_password_reset(self, email: str, code: str, new_password: str) -> bool:
        """
        Confirma o reset de senha com o código recebido
        :return: True se a confirmação for bem-sucedida
        """
        try:
            user = self.user_repository.get_user_by_email(email)

            VerificationCode = get_verification_code_model()
            is_valid = self.verification_repository.verify_code(
                user=user,
                code=code,
                code_type=VerificationCode.PASSWORD_RESET
            )

            if is_valid:
                # Atualiza a senha
                user.set_password(new_password)
                user.save()
                # Remove o código usado
                self.verification_repository.delete_code(user, VerificationCode.PASSWORD_RESET)
                return True
            
            return False
        except ObjectDoesNotExist:
            return False