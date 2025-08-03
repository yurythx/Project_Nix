# Repositories para o app config

from .config_repository import DjangoSystemConfigRepository
from .user_repository import DjangoUserRepository
from .permission_repository import DjangoPermissionRepository

__all__ = [
    'DjangoSystemConfigRepository',
    'DjangoUserRepository',
    'DjangoPermissionRepository',
]