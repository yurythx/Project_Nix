from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.db.models import QuerySet

User = get_user_model()

class IUserRepository(ABC):
    """Interface para repositório de usuários"""
    
    @abstractmethod
    def create(self, user_data: Dict[str, Any]) -> User:
        """Cria um novo usuário"""
        pass
    
    @abstractmethod
    def get_by_id(self, user_id: int) -> User:
        """Obtém usuário por ID"""
        pass
    
    @abstractmethod
    def get_by_email(self, email: str) -> User:
        """Obtém usuário por email"""
        pass
    
    @abstractmethod
    def update(self, user_id: int, user_data: Dict[str, Any]) -> User:
        """Atualiza usuário"""
        pass
    
    @abstractmethod
    def delete(self, user_id: int) -> bool:
        """Deleta usuário"""
        pass
    
    @abstractmethod
    def list_all(self, filters: Dict[str, Any] = None) -> QuerySet:
        """Lista todos os usuários com filtros opcionais"""
        pass
    
    @abstractmethod
    def search(self, query: str) -> QuerySet:
        """Busca usuários por termo"""
        pass
    
    @abstractmethod
    def exists_by_email(self, email: str) -> bool:
        """Verifica se existe usuário com o email"""
        pass
    
    @abstractmethod
    def exists_by_username(self, username: str) -> bool:
        """Verifica se existe usuário com o username"""
        pass

class IPermissionRepository(ABC):
    """Interface para repositório de permissões"""
    
    @abstractmethod
    def get_all_permissions(self) -> QuerySet:
        """Obtém todas as permissões"""
        pass
    
    @abstractmethod
    def get_permission_by_id(self, permission_id: int) -> Permission:
        """Obtém permissão por ID"""
        pass
    
    @abstractmethod
    def get_permissions_by_content_type(self, content_type: str) -> QuerySet:
        """Obtém permissões por tipo de conteúdo"""
        pass
    
    @abstractmethod
    def assign_permission_to_user(self, user: User, permission: Permission) -> bool:
        """Atribui permissão a usuário"""
        pass
    
    @abstractmethod
    def remove_permission_from_user(self, user: User, permission: Permission) -> bool:
        """Remove permissão de usuário"""
        pass
    
    @abstractmethod
    def get_user_permissions(self, user: User) -> QuerySet:
        """Obtém permissões do usuário"""
        pass

class IGroupRepository(ABC):
    """Interface para repositório de grupos"""
    
    @abstractmethod
    def get_all_groups(self) -> QuerySet:
        """Obtém todos os grupos"""
        pass
    
    @abstractmethod
    def get_group_by_id(self, group_id: int) -> Group:
        """Obtém grupo por ID"""
        pass
    
    @abstractmethod
    def get_group_by_name(self, name: str) -> Group:
        """Obtém grupo por nome"""
        pass
    
    @abstractmethod
    def create_group(self, name: str, permissions: List[Permission] = None) -> Group:
        """Cria novo grupo"""
        pass
    
    @abstractmethod
    def update_group(self, group_id: int, name: str = None, permissions: List[Permission] = None) -> Group:
        """Atualiza grupo"""
        pass
    
    @abstractmethod
    def delete_group(self, group_id: int) -> bool:
        """Deleta grupo"""
        pass
    
    @abstractmethod
    def assign_group_to_user(self, user: User, group: Group) -> bool:
        """Atribui grupo a usuário"""
        pass
    
    @abstractmethod
    def remove_group_from_user(self, user: User, group: Group) -> bool:
        """Remove grupo de usuário"""
        pass
    
    @abstractmethod
    def get_user_groups(self, user: User) -> QuerySet:
        """Obtém grupos do usuário"""
        pass

class ISystemConfigRepository(ABC):
    """Interface para repositório de configurações do sistema"""
    
    @abstractmethod
    def get_by_key(self, key: str) -> Any:
        """Obtém configuração por chave"""
        pass
    
    @abstractmethod
    def set_config(self, key: str, value: Any, description: str = "", updated_by: User = None) -> bool:
        """Define configuração"""
        pass
    
    @abstractmethod
    def delete_config(self, key: str) -> bool:
        """Deleta configuração"""
        pass
    
    @abstractmethod
    def list_all(self, active_only: bool = True) -> QuerySet:
        """Lista todas as configurações"""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Verifica se configuração existe"""
        pass

class IAuditLogRepository(ABC):
    """Interface para repositório de logs de auditoria"""
    
    @abstractmethod
    def create_log(self, user: User, action: str, target_user: User = None,
                  description: str = "", ip_address: str = None,
                  user_agent: str = None, extra_data: Dict = None) -> None:
        """Cria log de auditoria"""
        pass
    
    @abstractmethod
    def get_user_logs(self, user_id: int, limit: int = 100) -> QuerySet:
        """Obtém logs de um usuário"""
        pass
    
    @abstractmethod
    def get_system_logs(self, filters: Dict[str, Any] = None, limit: int = 100) -> QuerySet:
        """Obtém logs do sistema"""
        pass
    
    @abstractmethod
    def get_logs_by_action(self, action: str, limit: int = 100) -> QuerySet:
        """Obtém logs por tipo de ação"""
        pass
    
    @abstractmethod
    def get_logs_by_date_range(self, start_date, end_date, limit: int = 100) -> QuerySet:
        """Obtém logs por período"""
        pass
