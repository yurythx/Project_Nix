from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.db.models import QuerySet

User = get_user_model()

class IUserManagementService(ABC):
    """Interface para serviços de gerenciamento de usuários"""
    
    @abstractmethod
    def create_user(self, user_data: Dict[str, Any], created_by: User) -> User:
        """
        Cria um novo usuário
        :param user_data: Dados do usuário
        :param created_by: Usuário que está criando
        :return: Usuário criado
        """
        pass
    
    @abstractmethod
    def update_user(self, user_id: int, user_data: Dict[str, Any], updated_by: User) -> User:
        """
        Atualiza um usuário existente
        :param user_id: ID do usuário
        :param user_data: Dados para atualização
        :param updated_by: Usuário que está atualizando
        :return: Usuário atualizado
        """
        pass
    
    @abstractmethod
    def delete_user(self, user_id: int, deleted_by: User) -> bool:
        """
        Deleta um usuário
        :param user_id: ID do usuário
        :param deleted_by: Usuário que está deletando
        :return: True se deletado com sucesso
        """
        pass
    
    @abstractmethod
    def get_user_by_id(self, user_id: int) -> User:
        """
        Obtém um usuário pelo ID
        :param user_id: ID do usuário
        :return: Usuário encontrado
        """
        pass
    
    @abstractmethod
    def list_users(self, filters: Dict[str, Any] = None) -> QuerySet:
        """
        Lista usuários com filtros opcionais
        :param filters: Filtros para aplicar
        :return: QuerySet de usuários
        """
        pass
    
    @abstractmethod
    def search_users(self, query: str) -> QuerySet:
        """
        Busca usuários por termo
        :param query: Termo de busca
        :return: QuerySet de usuários encontrados
        """
        pass

class IPermissionManagementService(ABC):
    """Interface para serviços de gerenciamento de permissões"""
    
    @abstractmethod
    def assign_permission_to_user(self, user_id: int, permission_id: int, assigned_by: User) -> bool:
        """
        Atribui uma permissão a um usuário
        :param user_id: ID do usuário
        :param permission_id: ID da permissão
        :param assigned_by: Usuário que está atribuindo
        :return: True se atribuído com sucesso
        """
        pass
    
    @abstractmethod
    def remove_permission_from_user(self, user_id: int, permission_id: int, removed_by: User) -> bool:
        """
        Remove uma permissão de um usuário
        :param user_id: ID do usuário
        :param permission_id: ID da permissão
        :param removed_by: Usuário que está removendo
        :return: True se removido com sucesso
        """
        pass
    
    @abstractmethod
    def assign_group_to_user(self, user_id: int, group_id: int, assigned_by: User) -> bool:
        """
        Atribui um grupo a um usuário
        :param user_id: ID do usuário
        :param group_id: ID do grupo
        :param assigned_by: Usuário que está atribuindo
        :return: True se atribuído com sucesso
        """
        pass
    
    @abstractmethod
    def remove_group_from_user(self, user_id: int, group_id: int, removed_by: User) -> bool:
        """
        Remove um grupo de um usuário
        :param user_id: ID do usuário
        :param group_id: ID do grupo
        :param removed_by: Usuário que está removendo
        :return: True se removido com sucesso
        """
        pass
    
    @abstractmethod
    def get_user_permissions(self, user_id: int) -> List[Permission]:
        """
        Obtém todas as permissões de um usuário
        :param user_id: ID do usuário
        :return: Lista de permissões
        """
        pass
    
    @abstractmethod
    def get_user_groups(self, user_id: int) -> List[Group]:
        """
        Obtém todos os grupos de um usuário
        :param user_id: ID do usuário
        :return: Lista de grupos
        """
        pass

class ISystemConfigService(ABC):
    """Interface para serviços de configuração do sistema"""
    
    @abstractmethod
    def get_config(self, key: str) -> Any:
        """
        Obtém uma configuração pelo key
        :param key: Chave da configuração
        :return: Valor da configuração
        """
        pass
    
    @abstractmethod
    def set_config(self, key: str, value: Any, description: str = "", updated_by: User = None) -> bool:
        """
        Define uma configuração
        :param key: Chave da configuração
        :param value: Valor da configuração
        :param description: Descrição da configuração
        :param updated_by: Usuário que está atualizando
        :return: True se definido com sucesso
        """
        pass
    
    @abstractmethod
    def delete_config(self, key: str, deleted_by: User = None) -> bool:
        """
        Deleta uma configuração
        :param key: Chave da configuração
        :param deleted_by: Usuário que está deletando
        :return: True se deletado com sucesso
        """
        pass
    
    @abstractmethod
    def list_configs(self, active_only: bool = True) -> QuerySet:
        """
        Lista todas as configurações
        :param active_only: Se deve listar apenas configurações ativas
        :return: QuerySet de configurações
        """
        pass

class IAuditLogService(ABC):
    """Interface para serviços de log de auditoria"""
    
    @abstractmethod
    def log_user_action(self, user: User, action: str, target_user: User = None, 
                       description: str = "", ip_address: str = None, 
                       user_agent: str = None, extra_data: Dict = None) -> None:
        """
        Registra uma ação do usuário
        :param user: Usuário que executou a ação
        :param action: Tipo de ação
        :param target_user: Usuário alvo (se aplicável)
        :param description: Descrição da ação
        :param ip_address: Endereço IP
        :param user_agent: User agent
        :param extra_data: Dados extras
        """
        pass
    
    @abstractmethod
    def get_user_activity_logs(self, user_id: int, limit: int = 100) -> QuerySet:
        """
        Obtém logs de atividade de um usuário
        :param user_id: ID do usuário
        :param limit: Limite de registros
        :return: QuerySet de logs
        """
        pass
    
    @abstractmethod
    def get_system_activity_logs(self, filters: Dict[str, Any] = None, limit: int = 100) -> QuerySet:
        """
        Obtém logs de atividade do sistema
        :param filters: Filtros para aplicar
        :param limit: Limite de registros
        :return: QuerySet de logs
        """
        pass

class IModuleService(ABC):
    """Interface para serviços de gerenciamento de módulos"""
    
    @abstractmethod
    def get_all_modules(self) -> List[Any]:
        """
        Retorna todos os módulos
        :return: Lista de módulos
        """
        pass
    
    @abstractmethod
    def get_enabled_modules(self) -> List[Any]:
        """
        Retorna todos os módulos habilitados
        :return: Lista de módulos habilitados
        """
        pass
    
    @abstractmethod
    def get_available_modules(self) -> List[Any]:
        """
        Retorna módulos disponíveis para uso
        :return: Lista de módulos disponíveis
        """
        pass
    
    @abstractmethod
    def get_menu_modules(self) -> List[Any]:
        """
        Retorna módulos que devem aparecer no menu
        :return: Lista de módulos do menu
        """
        pass
    
    @abstractmethod
    def get_module_by_name(self, app_name: str) -> Optional[Any]:
        """
        Busca módulo por nome
        :param app_name: Nome do app
        :return: Módulo encontrado ou None
        """
        pass
    
    @abstractmethod
    def is_module_enabled(self, app_name: str) -> bool:
        """
        Verifica se um módulo está habilitado
        :param app_name: Nome do app
        :return: True se habilitado
        """
        pass
    
    @abstractmethod
    def is_core_module(self, app_name: str) -> bool:
        """
        Verifica se é um módulo principal
        :param app_name: Nome do app
        :return: True se for módulo principal
        """
        pass
    
    @abstractmethod
    def enable_module(self, app_name: str, user: User = None) -> bool:
        """
        Habilita um módulo
        :param app_name: Nome do app
        :param user: Usuário que está habilitando
        :return: True se habilitado com sucesso
        """
        pass
    
    @abstractmethod
    def disable_module(self, app_name: str, user: User = None) -> bool:
        """
        Desabilita um módulo
        :param app_name: Nome do app
        :param user: Usuário que está desabilitando
        :return: True se desabilitado com sucesso
        """
        pass
    
    @abstractmethod
    def create_module(self, module_data: Dict[str, Any], user: User = None) -> Optional[Any]:
        """
        Cria um novo módulo
        :param module_data: Dados do módulo
        :param user: Usuário que está criando
        :return: Módulo criado ou None
        """
        pass
    
    @abstractmethod
    def update_module(self, app_name: str, module_data: Dict[str, Any], user: User = None) -> bool:
        """
        Atualiza um módulo existente
        :param app_name: Nome do app
        :param module_data: Dados para atualização
        :param user: Usuário que está atualizando
        :return: True se atualizado com sucesso
        """
        pass
    
    @abstractmethod
    def get_module_statistics(self) -> Dict[str, Any]:
        """
        Retorna estatísticas dos módulos
        :return: Dicionário com estatísticas
        """
        pass

class IEmailConfigService(ABC):
    """Interface para serviços de configuração de email"""
    
    @abstractmethod
    def get_active_config(self) -> Dict[str, Any]:
        """
        Retorna a configuração de email ativa
        :return: Dicionário com configurações
        """
        pass
    
    @abstractmethod
    def get_connection(self, config: Dict[str, Any] = None) -> Any:
        """
        Cria conexão de email com configurações específicas
        :param config: Configurações de email
        :return: Conexão de email
        """
        pass
    
    @abstractmethod
    def test_connection(self, config: Dict[str, Any] = None) -> tuple[bool, str]:
        """
        Testa a conexão de email
        :param config: Configurações de email
        :return: Tupla (sucesso, mensagem)
        """
        pass
    
    @abstractmethod
    def apply_config_to_settings(self, config_dict: Dict[str, Any]) -> bool:
        """
        Aplica configurações dinamicamente ao Django settings
        :param config_dict: Configurações para aplicar
        :return: True se aplicado com sucesso
        """
        pass
    
    @abstractmethod
    def save_config(self, config_dict: Dict[str, Any], user: User = None, description: str = "") -> bool:
        """
        Salva configuração de email
        :param config_dict: Configurações para salvar
        :param user: Usuário que está salvando
        :param description: Descrição da configuração
        :return: True se salvo com sucesso
        """
        pass

class IDatabaseService(ABC):
    """Interface para serviços de configuração de banco de dados"""
    
    @abstractmethod
    def get_active_configuration(self) -> Any:
        """
        Retorna a configuração ativa
        :return: Configuração ativa
        """
        pass
    
    @abstractmethod
    def get_default_configuration(self) -> Any:
        """
        Retorna a configuração padrão
        :return: Configuração padrão
        """
        pass
    
    @abstractmethod
    def list_configurations(self) -> List[Any]:
        """
        Lista todas as configurações
        :return: Lista de configurações
        """
        pass
    
    @abstractmethod
    def create_configuration(self, name: str, engine: str, database_name: str, **kwargs) -> Any:
        """
        Cria uma nova configuração de banco
        :param name: Nome da configuração
        :param engine: Engine do banco
        :param database_name: Nome do banco
        :param kwargs: Outros parâmetros
        :return: Configuração criada
        """
        pass
    
    @abstractmethod
    def test_configuration(self, config_id: int) -> tuple[bool, str, Any]:
        """
        Testa uma configuração específica
        :param config_id: ID da configuração
        :return: Tupla (sucesso, mensagem, configuração)
        """
        pass
    
    @abstractmethod
    def activate_configuration(self, config_id: int, user: User = None) -> tuple[bool, str, Any]:
        """
        Ativa uma configuração específica
        :param config_id: ID da configuração
        :param user: Usuário que está ativando
        :return: Tupla (sucesso, mensagem, configuração)
        """
        pass
    
    @abstractmethod
    def switch_database(self, config_id: int, user: User = None) -> tuple[bool, str, Any]:
        """
        Troca o banco de dados ativo
        :param config_id: ID da configuração
        :param user: Usuário que está trocando
        :return: Tupla (sucesso, mensagem, configuração)
        """
        pass
