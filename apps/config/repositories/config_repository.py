from typing import Dict, Any
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import QuerySet
from apps.config.interfaces.repositories import ISystemConfigRepository, IAuditLogRepository
from apps.config.models import SystemConfiguration, UserActivityLog
import json

User = get_user_model()

class DjangoSystemConfigRepository(ISystemConfigRepository):
    """Implementação concreta do repositório de configurações do sistema"""
    
    def get_by_key(self, key: str) -> Any:
        """Obtém configuração por chave"""
        try:
            config = SystemConfiguration.objects.get(key=key, is_active=True)
            return config.get_value_as_json()
        except SystemConfiguration.DoesNotExist:
            raise ObjectDoesNotExist(f"Configuração com chave '{key}' não encontrada")
    
    def set_config(self, key: str, value: Any, description: str = "", updated_by: User = None) -> bool:
        """Define configuração"""
        try:
            # Converte valor para string se necessário
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value, ensure_ascii=False, indent=2)
            else:
                value_str = str(value)
            
            # Atualiza ou cria a configuração
            config, created = SystemConfiguration.objects.update_or_create(
                key=key,
                defaults={
                    'value': value_str,
                    'description': description,
                    'updated_by': updated_by,
                    'is_active': True
                }
            )
            return True
        except Exception as e:
            raise ValueError(f"Erro ao definir configuração: {str(e)}")
    
    def delete_config(self, key: str) -> bool:
        """Deleta configuração"""
        try:
            config = SystemConfiguration.objects.get(key=key)
            config.delete()
            return True
        except SystemConfiguration.DoesNotExist:
            return False
    
    def list_all(self, active_only: bool = True) -> QuerySet:
        """Lista todas as configurações"""
        queryset = SystemConfiguration.objects.all()
        if active_only:
            queryset = queryset.filter(is_active=True)
        return queryset.order_by('key')
    
    def exists(self, key: str) -> bool:
        """Verifica se configuração existe"""
        return SystemConfiguration.objects.filter(key=key).exists()


class DjangoAuditLogRepository(IAuditLogRepository):
    """Implementação concreta do repositório de logs de auditoria"""
    
    def create_log(self, user: User, action: str, target_user: User = None,
                  description: str = "", ip_address: str = None,
                  user_agent: str = None, extra_data: Dict = None) -> None:
        """Cria log de auditoria"""
        try:
            UserActivityLog.objects.create(
                user=user,
                action=action,
                target_user=target_user,
                description=description,
                ip_address=ip_address,
                user_agent=user_agent,
                extra_data=extra_data or {}
            )
        except Exception as e:
            # Log de auditoria não deve falhar a operação principal
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erro ao criar log de auditoria: {str(e)}")
    
    def get_user_logs(self, user_id: int, limit: int = 100) -> QuerySet:
        """Obtém logs de um usuário"""
        return UserActivityLog.objects.filter(
            user_id=user_id
        ).select_related('user', 'target_user').order_by('-created_at')[:limit]
    
    def get_system_logs(self, filters: Dict[str, Any] = None, limit: int = 100) -> QuerySet:
        """Obtém logs do sistema"""
        queryset = UserActivityLog.objects.all().select_related('user', 'target_user')
        
        if filters:
            # Filtro por ação
            if 'action' in filters:
                queryset = queryset.filter(action=filters['action'])
            
            # Filtro por usuário
            if 'user_id' in filters:
                queryset = queryset.filter(user_id=filters['user_id'])
            
            # Filtro por usuário alvo
            if 'target_user_id' in filters:
                queryset = queryset.filter(target_user_id=filters['target_user_id'])
            
            # Filtro por data
            if 'date_from' in filters:
                queryset = queryset.filter(created_at__gte=filters['date_from'])
            
            if 'date_to' in filters:
                queryset = queryset.filter(created_at__lte=filters['date_to'])
            
            # Filtro por IP
            if 'ip_address' in filters:
                queryset = queryset.filter(ip_address=filters['ip_address'])
        
        return queryset.order_by('-created_at')[:limit]
    
    def get_logs_by_action(self, action: str, limit: int = 100) -> QuerySet:
        """Obtém logs por tipo de ação"""
        return UserActivityLog.objects.filter(
            action=action
        ).select_related('user', 'target_user').order_by('-created_at')[:limit]
    
    def get_logs_by_date_range(self, start_date, end_date, limit: int = 100) -> QuerySet:
        """Obtém logs por período"""
        return UserActivityLog.objects.filter(
            created_at__range=[start_date, end_date]
        ).select_related('user', 'target_user').order_by('-created_at')[:limit]
