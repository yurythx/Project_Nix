from typing import List
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import QuerySet
from apps.config.interfaces.repositories import IPermissionRepository, IGroupRepository

User = get_user_model()

class DjangoPermissionRepository(IPermissionRepository):
    """Implementação concreta do repositório de permissões para Django"""
    
    def get_all_permissions(self) -> QuerySet:
        """Obtém todas as permissões"""
        return Permission.objects.all().select_related('content_type').order_by('content_type__app_label', 'codename')
    
    def get_permission_by_id(self, permission_id: int) -> Permission:
        """Obtém permissão por ID"""
        try:
            return Permission.objects.get(id=permission_id)
        except Permission.DoesNotExist:
            raise ObjectDoesNotExist(f"Permissão com ID {permission_id} não encontrada")
    
    def get_permissions_by_content_type(self, content_type: str) -> QuerySet:
        """Obtém permissões por tipo de conteúdo"""
        try:
            ct = ContentType.objects.get(app_label=content_type)
            return Permission.objects.filter(content_type=ct).order_by('codename')
        except ContentType.DoesNotExist:
            return Permission.objects.none()
    
    def assign_permission_to_user(self, user: User, permission: Permission) -> bool:
        """Atribui permissão a usuário"""
        try:
            user.user_permissions.add(permission)
            return True
        except Exception:
            return False
    
    def remove_permission_from_user(self, user: User, permission: Permission) -> bool:
        """Remove permissão de usuário"""
        try:
            user.user_permissions.remove(permission)
            return True
        except Exception:
            return False
    
    def get_user_permissions(self, user: User) -> QuerySet:
        """Obtém permissões do usuário"""
        return user.user_permissions.all().select_related('content_type').order_by('content_type__app_label', 'codename')


class DjangoGroupRepository(IGroupRepository):
    """Implementação concreta do repositório de grupos para Django"""
    
    def get_all_groups(self) -> QuerySet:
        """Obtém todos os grupos"""
        return Group.objects.all().prefetch_related('permissions').order_by('name')
    
    def get_group_by_id(self, group_id: int) -> Group:
        """Obtém grupo por ID"""
        try:
            return Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            raise ObjectDoesNotExist(f"Grupo com ID {group_id} não encontrado")
    
    def get_group_by_name(self, name: str) -> Group:
        """Obtém grupo por nome"""
        try:
            return Group.objects.get(name=name)
        except Group.DoesNotExist:
            raise ObjectDoesNotExist(f"Grupo com nome '{name}' não encontrado")
    
    def create_group(self, name: str, permissions: List[Permission] = None) -> Group:
        """Cria novo grupo"""
        try:
            group = Group.objects.create(name=name)
            if permissions:
                group.permissions.set(permissions)
            return group
        except Exception as e:
            raise ValueError(f"Erro ao criar grupo: {str(e)}")
    
    def update_group(self, group_id: int, name: str = None, permissions: List[Permission] = None) -> Group:
        """Atualiza grupo"""
        group = self.get_group_by_id(group_id)
        
        if name:
            group.name = name
            group.save()
        
        if permissions is not None:
            group.permissions.set(permissions)
        
        return group
    
    def delete_group(self, group_id: int) -> bool:
        """Deleta grupo"""
        try:
            group = self.get_group_by_id(group_id)
            group.delete()
            return True
        except ObjectDoesNotExist:
            return False
    
    def assign_group_to_user(self, user: User, group: Group) -> bool:
        """Atribui grupo a usuário"""
        try:
            user.groups.add(group)
            return True
        except Exception:
            return False
    
    def remove_group_from_user(self, user: User, group: Group) -> bool:
        """Remove grupo de usuário"""
        try:
            user.groups.remove(group)
            return True
        except Exception:
            return False
    
    def get_user_groups(self, user: User) -> QuerySet:
        """Obtém grupos do usuário"""
        return user.groups.all().prefetch_related('permissions').order_by('name')
