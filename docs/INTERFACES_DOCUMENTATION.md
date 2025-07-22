# Documentação das Interfaces - Django Skeleton

## 📋 Visão Geral

Este documento descreve todas as interfaces implementadas no projeto Django Skeleton, seguindo os princípios SOLID. As interfaces garantem contratos claros entre as camadas da aplicação e permitem fácil testabilidade e extensibilidade.

## 🏗️ Arquitetura de Interfaces

### **Estrutura de Camadas**

```
┌─────────────────┐
│     Views       │ ← Apresentação (usa Services via interfaces)
├─────────────────┤
│   Services      │ ← Lógica de Negócio (implementa interfaces)
├─────────────────┤
│  Interfaces     │ ← Contratos (definem comportamentos)
├─────────────────┤
│ Repositories    │ ← Acesso a Dados (implementa interfaces)
├─────────────────┤
│     Models      │ ← Entidades (Django ORM)
└─────────────────┘
```

## 📦 Interfaces por App

### **1. Accounts App**

#### **Services Interfaces**

##### `IRegistrationService`
```python
class IRegistrationService(ABC):
    def register_user(self, user_data: Dict[str, Any]) -> User
    def verify_registration(self, email: str, code: str) -> bool
    def resend_verification_code(self, email: str) -> bool
```

**Responsabilidade**: Gerenciar o processo de registro de usuários.

**Implementações**:
- `RegistrationService` - Implementação padrão

**Uso**:
```python
# Injeção de dependência
class RegistrationView(View):
    def __init__(self, registration_service: IRegistrationService = None):
        self.registration_service = registration_service or RegistrationService()
```

##### `IPasswordService`
```python
class IPasswordService(ABC):
    def change_password(self, user: User, old_password: str, new_password: str) -> bool
    def reset_password_request(self, email: str) -> bool
    def reset_password_confirm(self, email: str, code: str, new_password: str) -> bool
```

**Responsabilidade**: Gerenciar operações relacionadas a senhas.

**Implementações**:
- `PasswordService` - Implementação padrão

##### `IAuthService`
```python
class IAuthService(ABC):
    def authenticate_user(self, email: str, password: str) -> Optional[User]
    def logout_user(self, user: User) -> bool
```

**Responsabilidade**: Gerenciar autenticação de usuários.

**Implementações**:
- `AuthService` - Implementação padrão

##### `IProfileService`
```python
class IProfileService(ABC):
    def get_user_profile(self, user: User) -> Dict[str, Any]
    def update_user_profile(self, user: User, profile_data: Dict[str, Any]) -> bool
    def update_avatar(self, user: User, avatar_file) -> bool
    def delete_avatar(self, user: User) -> bool
```

**Responsabilidade**: Gerenciar perfis de usuários.

**Implementações**:
- `ProfileService` - Implementação padrão

##### `IEmailService`
```python
class IEmailService(ABC):
    def get_connection(self) -> Any
    def test_connection(self) -> tuple[bool, str]
    def send_email(self, subject: str, message: str, recipient_list: List[str], 
                   html_message: str = None, fail_silently: bool = False) -> bool
    def send_template_email(self, template_name: str, context: Dict[str, Any], 
                           subject: str, recipient_list: List[str], 
                           fail_silently: bool = False) -> bool
    def send_password_reset_code(self, email: str, code: str) -> bool
    def send_registration_confirmation(self, email: str, code: str) -> bool
    def send_test_email(self, recipient_email: str, user_name: str = None) -> bool
```

**Responsabilidade**: Gerenciar envio de emails.

**Implementações**:
- `EmailService` - Implementação padrão

#### **Repository Interfaces**

##### `IUserRepository`
```python
class IUserRepository(ABC):
    def get_by_id(self, user_id: int) -> Optional[User]
    def get_by_email(self, email: str) -> Optional[User]
    def create_user(self, user_data: Dict[str, Any]) -> User
    def update_user(self, user: User, user_data: Dict[str, Any]) -> User
    def delete_user(self, user: User) -> bool
    def list_users(self, filters: Dict[str, Any] = None) -> QuerySet
```

##### `IVerificationRepository`
```python
class IVerificationRepository(ABC):
    def create_verification(self, user: User, verification_type: str) -> Verification
    def get_verification(self, email: str, code: str, verification_type: str) -> Optional[Verification]
    def mark_verification_used(self, verification: Verification) -> bool
    def delete_expired_verifications(self) -> int
```

#### **Notification Interfaces**

##### `INotificationService`
```python
class INotificationService(ABC):
    def send_notification(self, user: User, message: str, notification_type: str) -> bool
    def send_bulk_notification(self, users: List[User], message: str, notification_type: str) -> bool
```

### **2. Articles App**

#### **Services Interfaces**

##### `IArticleService`
```python
class IArticleService(ABC):
    def get_published_articles(self) -> List[Article]
    def get_featured_articles(self, limit: int = 3) -> List[Article]
    def get_article_by_slug(self, slug: str) -> Optional[Article]
    def increment_article_views(self, article_id: int) -> bool
    def get_related_articles(self, article: Article, limit: int = 3) -> List[Article]
    def search_articles(self, query: str) -> List[Article]
    def create_article(self, article_data: Dict[str, Any], user: User) -> Optional[Article]
    def update_article(self, article_id: int, article_data: Dict[str, Any], user: User) -> bool
    def delete_article(self, article_id: int, user: User) -> bool
```

**Responsabilidade**: Gerenciar operações relacionadas a artigos.

**Implementações**:
- `ArticleService` - Implementação padrão

#### **Repository Interfaces**

##### `IArticleRepository`
```python
class IArticleRepository(ABC):
    def get_by_id(self, article_id: int) -> Optional[Article]
    def get_by_slug(self, slug: str) -> Optional[Article]
    def get_published_articles(self) -> QuerySet
    def get_featured_articles(self, limit: int = 3) -> QuerySet
    def search_articles(self, query: str) -> QuerySet
    def create_article(self, article_data: Dict[str, Any]) -> Article
    def update_article(self, article: Article, article_data: Dict[str, Any]) -> Article
    def delete_article(self, article: Article) -> bool
```

### **3. Config App**

#### **Services Interfaces**

##### `IUserManagementService`
```python
class IUserManagementService(ABC):
    def create_user(self, user_data: Dict[str, Any], created_by: User) -> User
    def update_user(self, user_id: int, user_data: Dict[str, Any], updated_by: User) -> User
    def delete_user(self, user_id: int, deleted_by: User) -> bool
    def get_user_by_id(self, user_id: int) -> User
    def list_users(self, filters: Dict[str, Any] = None) -> QuerySet
    def search_users(self, query: str) -> QuerySet
```

##### `IPermissionManagementService`
```python
class IPermissionManagementService(ABC):
    def assign_permission_to_user(self, user_id: int, permission_id: int, assigned_by: User) -> bool
    def remove_permission_from_user(self, user_id: int, permission_id: int, removed_by: User) -> bool
    def assign_group_to_user(self, user_id: int, group_id: int, assigned_by: User) -> bool
    def remove_group_from_user(self, user_id: int, group_id: int, removed_by: User) -> bool
    def get_user_permissions(self, user_id: int) -> List[Permission]
    def get_user_groups(self, user_id: int) -> List[Group]
```

##### `ISystemConfigService`
```python
class ISystemConfigService(ABC):
    def get_config(self, key: str) -> Any
    def set_config(self, key: str, value: Any, description: str = "", updated_by: User = None) -> bool
    def delete_config(self, key: str, deleted_by: User = None) -> bool
    def list_configs(self, active_only: bool = True) -> QuerySet
```

##### `IAuditLogService`
```python
class IAuditLogService(ABC):
    def log_user_action(self, user: User, action: str, target_user: User = None, 
                       description: str = "", ip_address: str = None, 
                       user_agent: str = None, extra_data: Dict = None) -> None
    def get_user_activity_logs(self, user_id: int, limit: int = 100) -> QuerySet
    def get_system_activity_logs(self, filters: Dict[str, Any] = None, limit: int = 100) -> QuerySet
```

##### `IModuleService`
```python
class IModuleService(ABC):
    def get_all_modules(self) -> List[Any]
    def get_enabled_modules(self) -> List[Any]
    def get_available_modules(self) -> List[Any]
    def get_menu_modules(self) -> List[Any]
    def get_module_by_name(self, app_name: str) -> Optional[Any]
    def is_module_enabled(self, app_name: str) -> bool
    def is_core_module(self, app_name: str) -> bool
    def enable_module(self, app_name: str, user: User = None) -> bool
    def disable_module(self, app_name: str, user: User = None) -> bool
    def create_module(self, module_data: Dict[str, Any], user: User = None) -> Optional[Any]
    def update_module(self, app_name: str, module_data: Dict[str, Any], user: User = None) -> bool
    def get_module_statistics(self) -> Dict[str, Any]
```

##### `IEmailConfigService`
```python
class IEmailConfigService(ABC):
    def get_active_config(self) -> Dict[str, Any]
    def get_connection(self, config: Dict[str, Any] = None) -> Any
    def test_connection(self, config: Dict[str, Any] = None) -> tuple[bool, str]
    def apply_config_to_settings(self, config_dict: Dict[str, Any]) -> bool
    def save_config(self, config_dict: Dict[str, Any], user: User = None, description: str = "") -> bool
```

##### `IDatabaseService`
```python
class IDatabaseService(ABC):
    def get_active_configuration(self) -> Any
    def get_default_configuration(self) -> Any
    def list_configurations(self) -> List[Any]
    def create_configuration(self, name: str, engine: str, database_name: str, **kwargs) -> Any
    def test_configuration(self, config_id: int) -> tuple[bool, str, Any]
    def activate_configuration(self, config_id: int, user: User = None) -> tuple[bool, str, Any]
    def switch_database(self, config_id: int, user: User = None) -> tuple[bool, str, Any]
```

#### **Repository Interfaces**

##### `IUserRepository`
```python
class IUserRepository(ABC):
    def get_by_id(self, user_id: int) -> Optional[User]
    def get_by_email(self, email: str) -> Optional[User]
    def create_user(self, user_data: Dict[str, Any]) -> User
    def update_user(self, user: User, user_data: Dict[str, Any]) -> User
    def delete_user(self, user: User) -> bool
    def list_users(self, filters: Dict[str, Any] = None) -> QuerySet
    def search_users(self, query: str) -> QuerySet
```

##### `IPermissionRepository`
```python
class IPermissionRepository(ABC):
    def get_permission_by_id(self, permission_id: int) -> Optional[Permission]
    def get_user_permissions(self, user: User) -> QuerySet
    def assign_permission_to_user(self, user: User, permission: Permission) -> bool
    def remove_permission_from_user(self, user: User, permission: Permission) -> bool
```

##### `ISystemConfigRepository`
```python
class ISystemConfigRepository(ABC):
    def get_by_key(self, key: str) -> Any
    def set_config(self, key: str, value: Any, description: str = "", updated_by: User = None) -> bool
    def delete_config(self, key: str, deleted_by: User = None) -> bool
    def list_configs(self, active_only: bool = True) -> QuerySet
    def exists(self, key: str) -> bool
    def list_all(self) -> QuerySet
```

#### **Middleware Interfaces**

##### `IModuleAccessMiddleware`
```python
class IModuleAccessMiddleware(ABC):
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]
    def is_path_exempt(self, path: str) -> bool
    def extract_app_name(self, path: str) -> Optional[str]
```

##### `IModuleContextMiddleware`
```python
class IModuleContextMiddleware(ABC):
    def process_template_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse
    def get_current_app(self, request: HttpRequest) -> Optional[str]
    def get_menu_modules(self) -> List[Any]
    def get_current_module(self, app_name: str) -> Optional[Any]
```

### **4. Pages App**

#### **Services Interfaces**

##### `IPageService`
```python
class IPageService(ABC):
    def get_page_by_slug(self, slug: str) -> Optional[Page]
    def get_published_pages(self) -> List[Page]
    def get_popular_pages(self, limit: int = 5) -> List[Page]
    def search_pages(self, query: str) -> List[Page]
    def increment_page_views(self, page_id: int) -> bool
    def get_breadcrumbs(self, page: Page) -> List[Dict[str, Any]]
    def create_page(self, page_data: Dict[str, Any], user: User) -> Optional[Page]
    def update_page(self, page_id: int, page_data: Dict[str, Any], user: User) -> bool
    def delete_page(self, page_id: int, user: User) -> bool
```

##### `INavigationService`
```python
class INavigationService(ABC):
    def get_main_navigation(self) -> List[NavigationItem]
    def get_footer_navigation(self) -> List[NavigationItem]
    def get_breadcrumbs(self, current_page: str) -> List[NavigationItem]
    def create_navigation_item(self, item_data: Dict[str, Any]) -> NavigationItem
    def update_navigation_item(self, item_id: int, item_data: Dict[str, Any]) -> bool
    def delete_navigation_item(self, item_id: int) -> bool
```

##### `ISEOService`
```python
class ISEOService(ABC):
    def get_seo_data(self, page: Page) -> Dict[str, Any]
    def update_seo_data(self, page: Page, seo_data: Dict[str, Any]) -> bool
    def generate_sitemap(self) -> str
    def get_meta_tags(self, page: Page) -> Dict[str, str]
```

#### **Repository Interfaces**

##### `IPageRepository`
```python
class IPageRepository(ABC):
    def get_by_id(self, page_id: int) -> Optional[Page]
    def get_by_slug(self, slug: str) -> Optional[Page]
    def get_published_pages(self) -> QuerySet
    def get_popular_pages(self, limit: int = 5) -> QuerySet
    def search_pages(self, query: str) -> QuerySet
    def create_page(self, page_data: Dict[str, Any]) -> Page
    def update_page(self, page: Page, page_data: Dict[str, Any]) -> Page
    def delete_page(self, page: Page) -> bool
```

## 🔧 Padrões de Uso

### **1. Injeção de Dependência**

```python
class ArticleListView(View):
    def __init__(self, article_service: IArticleService = None):
        super().__init__()
        # Injeção de dependência - usa service fornecido ou cria padrão
        self.article_service = article_service or ArticleService(DjangoArticleRepository())
    
    def get(self, request):
        articles = self.article_service.get_published_articles()
        # ... resto da lógica
```

### **2. Testes com Mocks**

```python
class MockArticleService(IArticleService):
    def __init__(self):
        self.articles = []
    
    def get_published_articles(self):
        return self.articles

class ArticleListViewTest(TestCase):
    def test_article_list_with_mock_service(self):
        mock_service = MockArticleService()
        view = ArticleListView(article_service=mock_service)
        # ... testes
```

### **3. Factory Pattern**

```python
class ServiceFactory:
    @staticmethod
    def create_article_service(repository: IArticleRepository = None) -> IArticleService:
        repo = repository or DjangoArticleRepository()
        return ArticleService(repo)
    
    @staticmethod
    def create_profile_service(user_repo: IUserRepository = None, 
                              email_service: IEmailService = None) -> IProfileService:
        user_repo = user_repo or DjangoUserRepository()
        email_service = email_service or EmailService()
        return ProfileService(user_repo, email_service)
```

## 📊 Benefícios das Interfaces

### **1. Testabilidade**
- ✅ Serviços podem ser testados isoladamente
- ✅ Mocks podem substituir implementações reais
- ✅ Testes LSP garantem contratos

### **2. Maintainability**
- ✅ Mudanças isoladas em uma camada
- ✅ Interfaces claras e documentadas
- ✅ Código mais legível e organizado

### **3. Extensibilidade**
- ✅ Novas implementações sem modificar código existente
- ✅ Plugins e extensões fáceis de adicionar
- ✅ Configurações flexíveis

### **4. Reusability**
- ✅ Serviços podem ser reutilizados em diferentes contextos
- ✅ Interfaces permitem diferentes implementações
- ✅ Lógica de negócio centralizada

## 🚀 Próximos Passos

### **1. Implementação de Factories**
- [ ] Criar factories para injeção de dependência
- [ ] Implementar container de dependências
- [ ] Configurar injeção automática

### **2. Testes de Integração**
- [ ] Expandir testes de integração
- [ ] Implementar testes de performance
- [ ] Adicionar testes de segurança

### **3. Documentação de APIs**
- [ ] Documentar APIs REST
- [ ] Criar exemplos de uso
- [ ] Documentar padrões de resposta

## 🚀 Exemplos de Integração

### ServiceFactory
```python
from core.factories import service_factory
article_service = service_factory.create_article_service()
profile_service = service_factory.create_profile_service()
```

### Observer/Dispatcher de Eventos
```python
from core.observers import event_dispatcher

def on_article_created(article):
    print(f"Novo artigo criado: {article.title}")

event_dispatcher.subscribe('article_created', on_article_created)
# ...
# Em algum ponto do código:
event_dispatcher.notify('article_created', article_instance)
```

---

**Última Atualização**: Dezembro 2024  
**Versão**: 1.0  
**Status**: ✅ Implementado 