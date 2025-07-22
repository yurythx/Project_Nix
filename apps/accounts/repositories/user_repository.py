from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model
from apps.accounts.interfaces.repositories import IUserRepository

User = get_user_model()

class DjangoUserRepository(IUserRepository):
    """Implementação concreta do repositório de usuários usando Django ORM"""
    
    def create_user(self, email: str, password: str, **extra_fields) -> User:
        """
        Cria um novo usuário com email e senha
        :raises ValueError: Se o usuário já existir
        """
        try:
            # Verifica se usuário já existe (case insensitive)
            existing_user = User.objects.filter(email__iexact=email).first()
            if existing_user:
                if existing_user.is_verified:
                    raise ValueError("Já existe um usuário verificado com este e-mail")
                # Se não estiver verificado, permite recriar (sobrescreve o anterior)
                existing_user.delete()
                
            return User.objects.create_user(
                email=email, 
                password=password, 
                **extra_fields
            )
        except Exception as e:
            raise ValueError(f"Erro ao criar usuário: {str(e)}")
    
    def get_user_by_email(self, email: str) -> User:
        """Obtém um usuário pelo email (case insensitive)"""
        try:
            return User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise ObjectDoesNotExist("Nenhum usuário encontrado com este e-mail")
    
    def get_user_by_slug(self, slug: str) -> User:
        """Obtém um usuário pelo slug"""
        try:
            return User.objects.get(slug=slug)
        except User.DoesNotExist:
            raise ObjectDoesNotExist("Nenhum usuário encontrado com este slug")
    
    def update_user(self, user: User, **fields) -> User:
        """Atualiza os campos de um usuário"""
        for field, value in fields.items():
            setattr(user, field, value)
        user.save()
        return user
    
    def exists_by_email(self, email: str) -> bool:
        """Verifica se existe um usuário com o email fornecido"""
        return User.objects.filter(email__iexact=email).exists()

    def exists_by_username(self, username: str) -> bool:
        """Verifica se existe um usuário com o username fornecido"""
        return User.objects.filter(username__iexact=username).exists()