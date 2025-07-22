from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class EmailOrUsernameModelBackend(ModelBackend):
    """
    Backend de autenticação personalizado que permite login com email ou username
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        try:
            # Tentar encontrar usuário por email ou username
            user = User.objects.get(
                Q(email__iexact=username) | Q(username__iexact=username)
            )
        except User.DoesNotExist:
            # Executar hash de senha padrão para reduzir diferença de tempo
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            # Se houver múltiplos usuários, tentar por email primeiro
            try:
                user = User.objects.get(email__iexact=username)
            except User.DoesNotExist:
                try:
                    user = User.objects.get(username__iexact=username)
                except User.DoesNotExist:
                    return None

        # Verificar senha e se o usuário pode ser autenticado
        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None

    def user_can_authenticate(self, user):
        """
        Rejeita usuários com is_active=False. Modelos de usuário personalizados
        que não têm esse atributo são permitidos.
        """
        is_active = getattr(user, 'is_active', True)
        return is_active


class EmailModelBackend(ModelBackend):
    """
    Backend de autenticação que usa apenas email (backup)
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        try:
            # Buscar apenas por email
            user = User.objects.get(email__iexact=username)
        except User.DoesNotExist:
            # Executar hash de senha padrão para reduzir diferença de tempo
            User().set_password(password)
            return None

        # Verificar senha e se o usuário pode ser autenticado
        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None


class UsernameModelBackend(ModelBackend):
    """
    Backend de autenticação que usa apenas username (backup)
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        try:
            # Buscar apenas por username
            user = User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            # Executar hash de senha padrão para reduzir diferença de tempo
            User().set_password(password)
            return None

        # Verificar senha e se o usuário pode ser autenticado
        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
