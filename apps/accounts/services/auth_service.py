from django.contrib.auth import authenticate, get_user_model
from apps.accounts.interfaces.services import IAuthService
from django.core.exceptions import ObjectDoesNotExist

User = get_user_model()

class AuthService(IAuthService):
    """Serviço para autenticação de usuários"""

    def __init__(self, user_repository):
        self.user_repository = user_repository

    def authenticate_user(self, email_or_username: str, password: str):
        """
        Autentica um usuário usando email ou username
        :return: Instância do usuário se autenticação for válida, None caso contrário
        :raises ValueError: Se o usuário não estiver verificado
        """
        user = self._authenticate_flexible(email_or_username, password)

        if user is None:
            return None

        if not user.is_verified:
            raise ValueError("Este usuário não está verificado. Por favor, verifique seu e-mail.")

        return user

    def _authenticate_flexible(self, username_or_email, password):
        """Autentica usuário por email ou username usando o backend personalizado"""

        # O backend personalizado já trata email e username automaticamente
        user = authenticate(
            username=username_or_email,
            password=password
        )

        return user