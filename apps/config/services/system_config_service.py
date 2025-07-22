from typing import Any
from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.db import transaction
from apps.config.interfaces.services import ISystemConfigService, IAuditLogService
from apps.config.interfaces.repositories import ISystemConfigRepository
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class SystemConfigService(ISystemConfigService):
    """Serviço para gerenciamento de configurações do sistema"""
    
    def __init__(self, config_repository: ISystemConfigRepository, audit_service: IAuditLogService):
        self.config_repository = config_repository
        self.audit_service = audit_service
    
    def get_config(self, key: str) -> Any:
        """
        Obtém uma configuração pelo key
        :param key: Chave da configuração
        :return: Valor da configuração
        """
        try:
            return self.config_repository.get_by_key(key)
        except Exception:
            return None
    
    @transaction.atomic
    def set_config(self, key: str, value: Any, description: str = "", updated_by: User = None) -> bool:
        """
        Define uma configuração
        :param key: Chave da configuração
        :param value: Valor da configuração
        :param description: Descrição da configuração
        :param updated_by: Usuário que está atualizando
        :return: True se definido com sucesso
        """
        try:
            # Verifica se é uma atualização ou criação
            is_update = self.config_repository.exists(key)
            old_value = None
            
            if is_update:
                try:
                    old_value = self.config_repository.get_by_key(key)
                except Exception:
                    old_value = None
            
            # Define a configuração
            success = self.config_repository.set_config(key, value, description, updated_by)
            
            if success and updated_by:
                # Log da ação
                action_type = 'UPDATE' if is_update else 'CREATE'
                self.audit_service.log_user_action(
                    user=updated_by,
                    action=action_type,
                    description=f"Configuração {'atualizada' if is_update else 'criada'}: {key}",
                    extra_data={
                        'config_key': key,
                        'new_value': str(value)[:200],  # Limita o tamanho do log
                        'old_value': str(old_value)[:200] if old_value else None,
                        'description': description
                    }
                )
                
                logger.info(f"Configuração {key} {'atualizada' if is_update else 'criada'} por {updated_by.email}")
            
            return success
        except Exception as e:
            logger.error(f"Erro ao definir configuração {key}: {str(e)}")
            return False
    
    @transaction.atomic
    def delete_config(self, key: str, deleted_by: User = None) -> bool:
        """
        Deleta uma configuração
        :param key: Chave da configuração
        :param deleted_by: Usuário que está deletando
        :return: True se deletado com sucesso
        """
        try:
            # Obtém o valor antes de deletar para log
            old_value = None
            try:
                old_value = self.config_repository.get_by_key(key)
            except Exception:
                pass
            
            # Deleta a configuração
            success = self.config_repository.delete_config(key)
            
            if success and deleted_by:
                # Log da ação
                self.audit_service.log_user_action(
                    user=deleted_by,
                    action='DELETE',
                    description=f"Configuração deletada: {key}",
                    extra_data={
                        'config_key': key,
                        'deleted_value': str(old_value)[:200] if old_value else None
                    }
                )
                
                logger.info(f"Configuração {key} deletada por {deleted_by.email}")
            
            return success
        except Exception as e:
            logger.error(f"Erro ao deletar configuração {key}: {str(e)}")
            return False
    
    def list_configs(self, active_only: bool = True) -> QuerySet:
        """
        Lista todas as configurações
        :param active_only: Se deve listar apenas configurações ativas
        :return: QuerySet de configurações
        """
        return self.config_repository.list_all(active_only)


class AuditLogService(IAuditLogService):
    """Serviço para logs de auditoria"""
    
    def __init__(self, audit_repository):
        self.audit_repository = audit_repository
    
    def log_user_action(self, user: User, action: str, target_user: User = None,
                       description: str = "", ip_address: str = None,
                       user_agent: str = None, extra_data: dict = None) -> None:
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
        try:
            self.audit_repository.create_log(
                user=user,
                action=action,
                target_user=target_user,
                description=description,
                ip_address=ip_address,
                user_agent=user_agent,
                extra_data=extra_data
            )
        except Exception as e:
            # Log de auditoria não deve falhar a operação principal
            logger.error(f"Erro ao criar log de auditoria: {str(e)}")
    
    def get_user_activity_logs(self, user_id: int, limit: int = 100) -> QuerySet:
        """
        Obtém logs de atividade de um usuário
        :param user_id: ID do usuário
        :param limit: Limite de registros
        :return: QuerySet de logs
        """
        return self.audit_repository.get_user_logs(user_id, limit)
    
    def get_system_activity_logs(self, filters: dict = None, limit: int = 100) -> QuerySet:
        """
        Obtém logs de atividade do sistema
        :param filters: Filtros para aplicar
        :param limit: Limite de registros
        :return: QuerySet de logs
        """
        return self.audit_repository.get_system_logs(filters, limit)
