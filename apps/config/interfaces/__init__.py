# Interfaces para o app config

from .repositories import (
    IUserRepository, IPermissionRepository, IGroupRepository, 
    ISystemConfigRepository, IAuditLogRepository
)
from .services import (
    IUserManagementService, IPermissionManagementService, 
    ISystemConfigService, IAuditLogService, IModuleService,
    IEmailConfigService, IDatabaseService
)

__all__ = [
    # Repositories
    'IUserRepository',
    'IPermissionRepository', 
    'IGroupRepository',
    'ISystemConfigRepository',
    'IAuditLogRepository',
    
    # Services
    'IUserManagementService',
    'IPermissionManagementService',
    'ISystemConfigService', 
    'IAuditLogService',
    'IModuleService',
    'IEmailConfigService',
    'IDatabaseService',
]
