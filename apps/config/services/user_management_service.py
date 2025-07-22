from typing import Dict, Any
from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.db import transaction
from apps.config.interfaces.services import IUserManagementService, IAuditLogService
from apps.config.interfaces.repositories import IUserRepository
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class UserManagementService(IUserManagementService):
    """
    Serviço para gerenciamento de usuários.
    Fornece métodos para criar, atualizar, deletar, buscar e listar usuários, com logging de auditoria.
    """
    
    def __init__(self, user_repository: IUserRepository, audit_service: IAuditLogService):
        self.user_repository = user_repository
        self.audit_service = audit_service
    
    @transaction.atomic
    def create_user(self, user_data: Dict[str, Any], created_by: User) -> User:
        """
        Cria um novo usuário
        :param user_data: Dados do usuário
        :param created_by: Usuário que está criando
        :return: Usuário criado
        """
        # Validações
        email = user_data.get('email')
        username = user_data.get('username')
        
        if not email:
            raise ValueError("Email é obrigatório")
        
        if not username:
            raise ValueError("Username é obrigatório")
        
        # Verifica se email já existe
        if self.user_repository.exists_by_email(email):
            raise ValueError(f"Já existe um usuário com o email {email}")
        
        # Verifica se username já existe
        if self.user_repository.exists_by_username(username):
            raise ValueError(f"Já existe um usuário com o username {username}")
        
        # Cria o usuário
        user = self.user_repository.create(user_data)
        
        # Log da ação
        self.audit_service.log_user_action(
            user=created_by,
            action='CREATE',
            target_user=user,
            description=f"Usuário criado: {user.email}",
            extra_data={'user_data': {k: v for k, v in user_data.items() if k != 'password'}}
        )
        
        logger.info(f"Usuário criado: {user.email} por {created_by.email}")
        return user
    
    @transaction.atomic
    def update_user(self, user_id: int, user_data: Dict[str, Any], updated_by: User) -> User:
        """
        Atualiza um usuário existente
        :param user_id: ID do usuário
        :param user_data: Dados para atualização
        :param updated_by: Usuário que está atualizando
        :return: Usuário atualizado
        """
        # Obtém o usuário
        user = self.user_repository.get_by_id(user_id)
        
        # Validações
        email = user_data.get('email')
        username = user_data.get('username')
        
        # Verifica se email já existe (exceto para o próprio usuário)
        if email and email != user.email and self.user_repository.exists_by_email(email):
            raise ValueError(f"Já existe um usuário com o email {email}")
        
        # Verifica se username já existe (exceto para o próprio usuário)
        if username and username != user.username and self.user_repository.exists_by_username(username):
            raise ValueError(f"Já existe um usuário com o username {username}")
        
        # Salva dados originais para log
        original_data = {
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser
        }
        
        # Atualiza o usuário
        updated_user = self.user_repository.update(user_id, user_data)
        
        # Log da ação
        self.audit_service.log_user_action(
            user=updated_by,
            action='UPDATE',
            target_user=updated_user,
            description=f"Usuário atualizado: {updated_user.email}",
            extra_data={
                'original_data': original_data,
                'updated_data': {k: v for k, v in user_data.items() if k != 'password'}
            }
        )
        
        logger.info(f"Usuário atualizado: {updated_user.email} por {updated_by.email}")
        return updated_user
    
    @transaction.atomic
    def delete_user(self, user_id: int, deleted_by: User) -> bool:
        """
        Deleta um usuário
        :param user_id: ID do usuário
        :param deleted_by: Usuário que está deletando
        :return: True se deletado com sucesso
        """
        # Obtém o usuário antes de deletar
        user = self.user_repository.get_by_id(user_id)
        
        # Não permite deletar superusuários
        if user.is_superuser:
            raise ValueError("Não é possível deletar superusuários")
        
        # Não permite deletar a si mesmo
        if user.id == deleted_by.id:
            raise ValueError("Não é possível deletar seu próprio usuário")
        
        # Salva dados para log
        user_data = {
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
        
        # Deleta o usuário
        success = self.user_repository.delete(user_id)
        
        if success:
            # Log da ação
            self.audit_service.log_user_action(
                user=deleted_by,
                action='DELETE',
                description=f"Usuário deletado: {user.email}",
                extra_data={'deleted_user_data': user_data}
            )
            
            logger.info(f"Usuário deletado: {user.email} por {deleted_by.email}")
        
        return success
    
    def get_user_by_id(self, user_id: int) -> User:
        """
        Obtém um usuário pelo ID
        :param user_id: ID do usuário
        :return: Usuário encontrado
        """
        return self.user_repository.get_by_id(user_id)
    
    def list_users(self, filters: Dict[str, Any] = None) -> QuerySet:
        """
        Lista usuários com filtros opcionais
        :param filters: Filtros para aplicar
        :return: QuerySet de usuários
        """
        return self.user_repository.list_all(filters)
    
    def search_users(self, query: str) -> QuerySet:
        """
        Busca usuários por termo
        :param query: Termo de busca
        :return: QuerySet de usuários encontrados
        """
        return self.user_repository.search(query)
