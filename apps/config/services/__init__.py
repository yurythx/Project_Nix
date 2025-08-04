# Services para o app config

from .module_service import ModuleService
from .user_management_service import UserManagementService
from .permission_management_service import PermissionManagementService
from .system_config_service import SystemConfigService, AuditLogService
from .email_config_service import DynamicEmailConfigService
from .database_service import DatabaseService
from .group_service import GroupService
from .backup_service import BackupService

# Alias para compatibilidade
AuditService = AuditLogService

# Import do EmailService do app accounts
from apps.accounts.services.email_service import EmailService

__all__ = [
    'ModuleService',
    'UserManagementService', 
    'PermissionManagementService',
    'SystemConfigService',
    'DynamicEmailConfigService',
    'DatabaseService',
    'GroupService',
    'BackupService',
    'AuditService',  # Alias para AuditLogService
    'AuditLogService',
    'EmailService'  # Importado do app accounts
]