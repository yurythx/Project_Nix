from typing import Dict, Any
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q, QuerySet
from apps.config.interfaces.repositories import IUserRepository

User = get_user_model()

class DjangoUserRepository(IUserRepository):
    """Implementação concreta do repositório de usuários para Django"""
    
    def create(self, user_data: Dict[str, Any]) -> User:
        """Cria um novo usuário"""
        try:
            # Extrai a senha se fornecida
            password = user_data.pop('password', None)
            # NÃO remova is_verified do user_data
            # Cria o usuário
            user = User.objects.create_user(**user_data)
            # Define a senha se fornecida
            if password:
                user.set_password(password)
                user.save()
            return user
        except Exception as e:
            raise ValueError(f"Erro ao criar usuário: {str(e)}")
    
    def get_by_id(self, user_id: int) -> User:
        """Obtém usuário por ID"""
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise ObjectDoesNotExist(f"Usuário com ID {user_id} não encontrado")
    
    def get_by_email(self, email: str) -> User:
        """Obtém usuário por email"""
        try:
            return User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise ObjectDoesNotExist(f"Usuário com email {email} não encontrado")
    
    def update(self, user_id: int, user_data: Dict[str, Any]) -> User:
        """Atualiza usuário"""
        user = self.get_by_id(user_id)
        
        # Remove campos que não devem ser atualizados diretamente
        password = user_data.pop('password', None)
        
        # Atualiza os campos
        for field, value in user_data.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        # Atualiza a senha se fornecida
        if password:
            user.set_password(password)
        
        user.save()
        return user
    
    def delete(self, user_id: int) -> bool:
        """Deleta usuário"""
        try:
            user = self.get_by_id(user_id)
            user.delete()
            return True
        except ObjectDoesNotExist:
            return False
    
    def list_all(self, filters: Dict[str, Any] = None) -> QuerySet:
        """Lista todos os usuários com filtros opcionais"""
        queryset = User.objects.all()
        
        if filters:
            # Filtro por status ativo
            if 'is_active' in filters:
                queryset = queryset.filter(is_active=filters['is_active'])
            
            # Filtro por staff
            if 'is_staff' in filters:
                queryset = queryset.filter(is_staff=filters['is_staff'])
            
            # Filtro por superuser
            if 'is_superuser' in filters:
                queryset = queryset.filter(is_superuser=filters['is_superuser'])
            
            # Filtro por verificado
            if 'is_verified' in filters:
                queryset = queryset.filter(is_verified=filters['is_verified'])
            
            # Filtro por data de criação
            if 'date_joined_from' in filters:
                queryset = queryset.filter(date_joined__gte=filters['date_joined_from'])
            
            if 'date_joined_to' in filters:
                queryset = queryset.filter(date_joined__lte=filters['date_joined_to'])
        
        return queryset.order_by('-date_joined')
    
    def search(self, query: str) -> QuerySet:
        """Busca usuários por termo"""
        if not query:
            return User.objects.none()
        
        return User.objects.filter(
            Q(email__icontains=query) |
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        ).order_by('-date_joined')
    
    def exists_by_email(self, email: str) -> bool:
        """Verifica se existe usuário com o email"""
        return User.objects.filter(email__iexact=email).exists()
    
    def exists_by_username(self, username: str) -> bool:
        """Verifica se existe usuário com o username"""
        return User.objects.filter(username__iexact=username).exists()
