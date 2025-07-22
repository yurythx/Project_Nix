"""
ServiceFactory - Fábrica central de serviços do projeto

- Serviços obrigatórios: RegistrationService, PasswordService, AuthService, ProfileService, EmailService, ArticleService, PageService
- Serviços opcionais: NavigationService, SEOService, UserManagementService, PermissionManagementService, SystemConfigService, ModuleService, EmailConfigService, DatabaseService

- Em ambiente de desenvolvimento/teste, faz fallback para mocks/stubs se serviço não existir
- Permite registro dinâmico de serviços customizados

Exemplo de uso:
from core.factories import service_factory
article_service = service_factory.create_article_service()

"""

from typing import Dict, Any, Optional, Type
from django.conf import settings
from django.core.cache import cache
import importlib
import logging

logger = logging.getLogger(__name__)

# Imports obrigatórios
from apps.accounts.services.registration_service import RegistrationService
from apps.accounts.services.password_service import PasswordService
from apps.accounts.services.auth_service import AuthService
from apps.accounts.services.profile_service import ProfileService
from apps.accounts.services.email_service import EmailService
from apps.articles.services.article_service import ArticleService
from apps.pages.services.page_service import PageService

# Imports opcionais com tratamento
try:
    from apps.pages.services.navigation_service import NavigationService
except ImportError:
    NavigationService = None
try:
    from apps.pages.services.seo_service import SEOService
except ImportError:
    SEOService = None
try:
    from apps.config.services.user_management_service import UserManagementService
except ImportError:
    UserManagementService = None
try:
    from apps.config.services.permission_management_service import PermissionManagementService
except ImportError:
    PermissionManagementService = None
try:
    from apps.config.services.system_config_service import SystemConfigService
except ImportError:
    SystemConfigService = None
try:
    from apps.config.services.module_service import ModuleService
except ImportError:
    ModuleService = None
try:
    from apps.config.services.email_config_service import EmailConfigService
except ImportError:
    EmailConfigService = None
try:
    from apps.config.services.database_service import DatabaseService
except ImportError:
    DatabaseService = None

# Imports dos Repositories (obrigatórios)
from apps.accounts.repositories.user_repository import DjangoUserRepository
from apps.accounts.repositories.verification_repository import DjangoVerificationRepository
from apps.articles.repositories.article_repository import DjangoArticleRepository
from apps.pages.repositories.page_repository import DjangoPageRepository
from apps.pages.repositories.seo_repository import DjangoSEORepository
from apps.config.repositories.user_repository import DjangoUserRepository as DjangoConfigUserRepository

# Interfaces
from apps.accounts.interfaces.services import (
    IRegistrationService, IPasswordService, IAuthService, 
    IProfileService, IEmailService
)
from apps.accounts.interfaces.repositories import IUserRepository, IVerificationRepository
from apps.articles.interfaces.services import IArticleService
from apps.articles.interfaces.repositories import IArticleRepository
from apps.pages.interfaces.services import IPageService, ISEOService
from apps.pages.interfaces.repositories import IPageRepository, ISEORepository
from apps.config.interfaces.repositories import IUserRepository as IConfigUserRepository, IPermissionRepository, ISystemConfigRepository
from apps.config.interfaces.services import IUserManagementService, IPermissionManagementService, ISystemConfigService, IModuleService, IEmailConfigService, IDatabaseService

class ServiceFactory:
    """
    Factory para criação de serviços com injeção de dependências
    Implementa padrão Singleton para cache de instâncias
    Permite fallback para mocks em dev/test
    Permite registro dinâmico de serviços customizados
    """
    _instance = None
    _services_cache: Dict[str, Any] = {}
    _custom_services: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._initialize_repositories()
            self._load_custom_config()
    
    def _initialize_repositories(self):
        self._repositories = {
            'user_repository': DjangoUserRepository(),
            'verification_repository': DjangoVerificationRepository(),
            'article_repository': DjangoArticleRepository(),
            'page_repository': DjangoPageRepository(),
            'seo_repository': DjangoSEORepository(),
            'config_user_repository': DjangoConfigUserRepository(),
        }
    
    def _load_custom_config(self):
        self.custom_implementations = getattr(settings, 'SERVICE_OVERRIDES', {})
    
    def get_repository(self, repository_type: str):
        return self._repositories.get(repository_type)
    
    def register_service(self, interface_name: str, implementation):
        """Permite registrar serviço customizado em runtime"""
        self._custom_services[interface_name] = implementation
    
    def _get_implementation_class(self, interface_name: str, default_class):
        # 1. Verifica registro dinâmico
        if interface_name in self._custom_services:
            return self._custom_services[interface_name]
        # 2. Verifica settings
        custom_class = self.custom_implementations.get(interface_name)
        if custom_class:
            module_path, class_name = custom_class.rsplit('.', 1)
            module = importlib.import_module(module_path)
            return getattr(module, class_name)
        # 3. Fallback para default
        return default_class
    
    def create_article_service(self, article_repository: IArticleRepository = None) -> IArticleService:
        cache_key = f"article_service_{id(article_repository)}"
        if cache_key not in self._services_cache:
            article_repo = article_repository or self.get_repository('article_repository')
            service_class = self._get_implementation_class('IArticleService', ArticleService)
            self._services_cache[cache_key] = service_class(article_repository=article_repo)
        return self._services_cache[cache_key]
    
    def create_registration_service(self, 
                                  user_repository: IUserRepository = None,
                                  verification_repository: IVerificationRepository = None,
                                  email_service: IEmailService = None) -> IRegistrationService:
        """Cria RegistrationService com dependências injetadas"""
        cache_key = f"registration_service_{id(user_repository)}_{id(verification_repository)}_{id(email_service)}"
        
        if cache_key not in self._services_cache:
            user_repo = user_repository or self.get_repository('user_repository')
            verification_repo = verification_repository or self.get_repository('verification_repository')
            email_svc = email_service or self.create_email_service()
            
            self._services_cache[cache_key] = RegistrationService(
                user_repository=user_repo,
                verification_repository=verification_repo,
                email_service=email_svc
            )
        
        return self._services_cache[cache_key]
    
    def create_password_service(self, 
                              user_repository: IUserRepository = None,
                              email_service: IEmailService = None) -> IPasswordService:
        """Cria PasswordService com dependências injetadas"""
        cache_key = f"password_service_{id(user_repository)}_{id(email_service)}"
        
        if cache_key not in self._services_cache:
            user_repo = user_repository or self.get_repository('user_repository')
            email_svc = email_service or self.create_email_service()
            
            self._services_cache[cache_key] = PasswordService(
                user_repository=user_repo,
                email_service=email_svc
            )
        
        return self._services_cache[cache_key]
    
    def create_auth_service(self, 
                          user_repository: IUserRepository = None) -> IAuthService:
        """Cria AuthService com dependências injetadas"""
        cache_key = f"auth_service_{id(user_repository)}"
        
        if cache_key not in self._services_cache:
            user_repo = user_repository or self.get_repository('user_repository')
            
            self._services_cache[cache_key] = AuthService(
                user_repository=user_repo
            )
        
        return self._services_cache[cache_key]
    
    def create_profile_service(self, 
                             user_repository: IUserRepository = None,
                             email_service: IEmailService = None) -> IProfileService:
        """Cria ProfileService com dependências injetadas"""
        cache_key = f"profile_service_{id(user_repository)}_{id(email_service)}"
        
        if cache_key not in self._services_cache:
            user_repo = user_repository or self.get_repository('user_repository')
            email_svc = email_service or self.create_email_service()
            
            self._services_cache[cache_key] = ProfileService(
                user_repository=user_repo,
                email_service=email_svc
            )
        
        return self._services_cache[cache_key]
    
    def create_email_service(self) -> IEmailService:
        """Cria EmailService"""
        cache_key = "email_service"
        
        if cache_key not in self._services_cache:
            self._services_cache[cache_key] = EmailService()
        
        return self._services_cache[cache_key]
    
    def create_page_service(self, 
                          page_repository: IPageRepository = None) -> IPageService:
        """Cria PageService com dependências injetadas"""
        cache_key = f"page_service_{id(page_repository)}"
        
        if cache_key not in self._services_cache:
            page_repo = page_repository or self.get_repository('page_repository')
            
            self._services_cache[cache_key] = PageService(
                page_repository=page_repo
            )
        
        return self._services_cache[cache_key]
    
    def create_navigation_service(self):
        if NavigationService:
            return NavigationService()
        logger.warning('NavigationService não disponível, usando mock')
        return lambda *a, **kw: None
    
    def create_seo_service(self, 
                          seo_repository: ISEORepository = None) -> ISEOService:
        """Cria SEOService com dependências injetadas"""
        cache_key = f"seo_service_{id(seo_repository)}"
        
        if cache_key not in self._services_cache:
            seo_repo = seo_repository or self.get_repository('seo_repository')
            
            self._services_cache[cache_key] = SEOService(
                seo_repository=seo_repo
            )
        
        return self._services_cache[cache_key]
    
    def create_user_management_service(self, 
                                     user_repository: IConfigUserRepository = None) -> IUserManagementService:
        """Cria UserManagementService com dependências injetadas"""
        cache_key = f"user_management_service_{id(user_repository)}"
        
        if cache_key not in self._services_cache:
            user_repo = user_repository or self.get_repository('config_user_repository')
            
            self._services_cache[cache_key] = UserManagementService(
                user_repository=user_repo
            )
        
        return self._services_cache[cache_key]
    
    def create_permission_management_service(self, 
                                           permission_repository: IPermissionRepository = None) -> IPermissionManagementService:
        """Cria PermissionManagementService com dependências injetadas"""
        cache_key = f"permission_management_service_{id(permission_repository)}"
        
        if cache_key not in self._services_cache:
            perm_repo = permission_repository or self.get_repository('permission_repository')
            
            self._services_cache[cache_key] = PermissionManagementService(
                permission_repository=perm_repo
            )
        
        return self._services_cache[cache_key]
    
    def create_system_config_service(self, 
                                   config_repository: ISystemConfigRepository = None) -> ISystemConfigService:
        """Cria SystemConfigService com dependências injetadas"""
        cache_key = f"system_config_service_{id(config_repository)}"
        
        if cache_key not in self._services_cache:
            config_repo = config_repository or self.get_repository('system_config_repository')
            
            self._services_cache[cache_key] = SystemConfigService(
                config_repository=config_repo
            )
        
        return self._services_cache[cache_key]
    
    def create_module_service(self) -> IModuleService:
        """Cria ModuleService"""
        cache_key = "module_service"
        
        if cache_key not in self._services_cache:
            self._services_cache[cache_key] = ModuleService()
        
        return self._services_cache[cache_key]
    
    def create_email_config_service(self) -> IEmailConfigService:
        """Cria EmailConfigService"""
        cache_key = "email_config_service"
        
        if cache_key not in self._services_cache:
            self._services_cache[cache_key] = EmailConfigService()
        
        return self._services_cache[cache_key]
    
    def create_database_service(self) -> IDatabaseService:
        """Cria DatabaseService"""
        cache_key = "database_service"
        
        if cache_key not in self._services_cache:
            self._services_cache[cache_key] = DatabaseService()
        
        return self._services_cache[cache_key]
    
    def clear_cache(self):
        """Limpa o cache de serviços"""
        self._services_cache.clear()
    
    def get_cached_services(self) -> Dict[str, Any]:
        """Retorna serviços em cache para debugging"""
        return self._services_cache.copy()


# Instância global do factory
service_factory = ServiceFactory() 