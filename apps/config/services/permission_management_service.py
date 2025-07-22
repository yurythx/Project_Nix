from typing import List
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.db import transaction
from apps.config.interfaces.services import IPermissionManagementService, IAuditLogService
from apps.config.interfaces.repositories import IUserRepository, IPermissionRepository, IGroupRepository
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class PermissionManagementService(IPermissionManagementService):
    """Serviço para gerenciamento de permissões"""
    
    def __init__(self, user_repository: IUserRepository, 
                 permission_repository: IPermissionRepository,
                 group_repository: IGroupRepository,
                 audit_service: IAuditLogService):
        self.user_repository = user_repository
        self.permission_repository = permission_repository
        self.group_repository = group_repository
        self.audit_service = audit_service
    
    @transaction.atomic
    def assign_permission_to_user(self, user_id: int, permission_id: int, assigned_by: User) -> bool:
        """
        Atribui uma permissão a um usuário
        :param user_id: ID do usuário
        :param permission_id: ID da permissão
        :param assigned_by: Usuário que está atribuindo
        :return: True se atribuído com sucesso
        """
        user = self.user_repository.get_by_id(user_id)
        permission = self.permission_repository.get_permission_by_id(permission_id)
        
        # Verifica se o usuário já tem a permissão
        if user.user_permissions.filter(id=permission_id).exists():
            raise ValueError(f"Usuário {user.email} já possui a permissão {permission.name}")
        
        # Atribui a permissão
        success = self.permission_repository.assign_permission_to_user(user, permission)
        
        if success:
            # Log da ação
            self.audit_service.log_user_action(
                user=assigned_by,
                action='PERMISSION_CHANGE',
                target_user=user,
                description=f"Permissão atribuída: {permission.name} para {user.email}",
                extra_data={
                    'permission_id': permission_id,
                    'permission_name': permission.name,
                    'action_type': 'assign'
                }
            )
            
            logger.info(f"Permissão {permission.name} atribuída para {user.email} por {assigned_by.email}")
        
        return success
    
    @transaction.atomic
    def remove_permission_from_user(self, user_id: int, permission_id: int, removed_by: User) -> bool:
        """
        Remove uma permissão de um usuário
        :param user_id: ID do usuário
        :param permission_id: ID da permissão
        :param removed_by: Usuário que está removendo
        :return: True se removido com sucesso
        """
        user = self.user_repository.get_by_id(user_id)
        permission = self.permission_repository.get_permission_by_id(permission_id)
        
        # Verifica se o usuário tem a permissão
        if not user.user_permissions.filter(id=permission_id).exists():
            raise ValueError(f"Usuário {user.email} não possui a permissão {permission.name}")
        
        # Remove a permissão
        success = self.permission_repository.remove_permission_from_user(user, permission)
        
        if success:
            # Log da ação
            self.audit_service.log_user_action(
                user=removed_by,
                action='PERMISSION_CHANGE',
                target_user=user,
                description=f"Permissão removida: {permission.name} de {user.email}",
                extra_data={
                    'permission_id': permission_id,
                    'permission_name': permission.name,
                    'action_type': 'remove'
                }
            )
            
            logger.info(f"Permissão {permission.name} removida de {user.email} por {removed_by.email}")
        
        return success
    
    @transaction.atomic
    def assign_group_to_user(self, user_id: int, group_id: int, assigned_by: User) -> bool:
        """
        Atribui um grupo a um usuário
        :param user_id: ID do usuário
        :param group_id: ID do grupo
        :param assigned_by: Usuário que está atribuindo
        :return: True se atribuído com sucesso
        """
        user = self.user_repository.get_by_id(user_id)
        group = self.group_repository.get_group_by_id(group_id)
        
        # Verifica se o usuário já está no grupo
        if user.groups.filter(id=group_id).exists():
            raise ValueError(f"Usuário {user.email} já pertence ao grupo {group.name}")
        
        # Atribui o grupo
        success = self.group_repository.assign_group_to_user(user, group)
        
        if success:
            # Log da ação
            self.audit_service.log_user_action(
                user=assigned_by,
                action='GROUP_CHANGE',
                target_user=user,
                description=f"Grupo atribuído: {group.name} para {user.email}",
                extra_data={
                    'group_id': group_id,
                    'group_name': group.name,
                    'action_type': 'assign'
                }
            )
            
            logger.info(f"Grupo {group.name} atribuído para {user.email} por {assigned_by.email}")
        
        return success
    
    @transaction.atomic
    def remove_group_from_user(self, user_id: int, group_id: int, removed_by: User) -> bool:
        """
        Remove um grupo de um usuário
        :param user_id: ID do usuário
        :param group_id: ID do grupo
        :param removed_by: Usuário que está removendo
        :return: True se removido com sucesso
        """
        user = self.user_repository.get_by_id(user_id)
        group = self.group_repository.get_group_by_id(group_id)
        
        # Verifica se o usuário está no grupo
        if not user.groups.filter(id=group_id).exists():
            raise ValueError(f"Usuário {user.email} não pertence ao grupo {group.name}")
        
        # Remove o grupo
        success = self.group_repository.remove_group_from_user(user, group)
        
        if success:
            # Log da ação
            self.audit_service.log_user_action(
                user=removed_by,
                action='GROUP_CHANGE',
                target_user=user,
                description=f"Grupo removido: {group.name} de {user.email}",
                extra_data={
                    'group_id': group_id,
                    'group_name': group.name,
                    'action_type': 'remove'
                }
            )
            
            logger.info(f"Grupo {group.name} removido de {user.email} por {removed_by.email}")
        
        return success
    
    def get_user_permissions(self, user_id: int) -> List[Permission]:
        """
        Obtém todas as permissões de um usuário
        :param user_id: ID do usuário
        :return: Lista de permissões
        """
        user = self.user_repository.get_by_id(user_id)
        
        # Obtém permissões diretas
        direct_permissions = list(self.permission_repository.get_user_permissions(user))
        
        # Obtém permissões dos grupos
        group_permissions = []
        for group in user.groups.all():
            group_permissions.extend(list(group.permissions.all()))
        
        # Remove duplicatas
        all_permissions = list(set(direct_permissions + group_permissions))
        
        return sorted(all_permissions, key=lambda p: (p.content_type.app_label, p.codename))
    
    def get_user_groups(self, user_id: int) -> List[Group]:
        """
        Obtém todos os grupos de um usuário
        :param user_id: ID do usuário
        :return: Lista de grupos
        """
        user = self.user_repository.get_by_id(user_id)
        return list(self.group_repository.get_user_groups(user))
