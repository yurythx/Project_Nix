# 🏗️ Arquitetura Project Nix

## 📋 Visão Geral

O **Project Nix** é construído sobre uma arquitetura robusta baseada nos princípios SOLID, utilizando padrões de design modernos e uma estrutura modular que permite escalabilidade e manutenibilidade.

## 🎯 Princípios Arquiteturais

### **SOLID Principles**
- **S** - Single Responsibility Principle
- **O** - Open/Closed Principle  
- **L** - Liskov Substitution Principle
- **I** - Interface Segregation Principle
- **D** - Dependency Inversion Principle

### **Padrões de Design**
- **Factory Pattern**: Criação de objetos complexos
- **Observer Pattern**: Sistema de eventos e notificações
- **Repository Pattern**: Abstração de acesso a dados
- **Service Layer**: Lógica de negócio centralizada
- **Dependency Injection**: Inversão de controle

## 🏗️ Camadas da Arquitetura

### **1. Presentation Layer (Apresentação)**
```
apps/
├── pages/          # Páginas estáticas e dinâmicas
├── accounts/       # Autenticação e perfis
├── articles/       # Sistema de artigos
├── books/          # Gerenciamento de livros
├── mangas/         # Sistema de mangás
└── audiobooks/     # Sistema de audiolivros
```

**Responsabilidades:**
- Templates HTML
- Views (Class-Based Views)
- Forms
- URLs e roteamento
- Middleware de apresentação

### **2. Business Layer (Negócio)**
```
apps/*/services/
├── article_service.py
├── user_service.py
├── module_service.py
└── notification_service.py
```

**Responsabilidades:**
- Lógica de negócio
- Validações complexas
- Orquestração de operações
- Regras de negócio

### **3. Data Access Layer (Acesso a Dados)**
```
apps/*/repositories/
├── article_repository.py
├── user_repository.py
└── module_repository.py
```

**Responsabilidades:**
- Abstração de acesso a dados
- Queries complexas
- Cache de dados
- Transações

### **4. Infrastructure Layer (Infraestrutura)**
```
core/
├── settings.py
├── urls.py
├── wsgi.py
├── cache.py
├── performance.py
└── security.py
```

**Responsabilidades:**
- Configurações do sistema
- Middleware de infraestrutura
- Cache e performance
- Segurança e autenticação

## 🔌 Sistema de Módulos

### **Tipos de Módulos**

#### **Core Modules (Principais)**
- `accounts`: Sistema de usuários (sempre ativo)
- `config`: Configurações do sistema (sempre ativo)
- `pages`: Páginas estáticas (sempre ativo)

#### **Feature Modules (Funcionalidades)**
- `articles`: Sistema de artigos
- `books`: Gerenciamento de livros
- `mangas`: Sistema de mangás
- `audiobooks`: Sistema de audiolivros

#### **Integration Modules (Integrações)**
- `api`: API REST (futuro)
- `notifications`: Sistema de notificações (futuro)
- `analytics`: Analytics e métricas (futuro)

### **Controle de Módulos**
```python
# apps/config/models/app_module_config.py
class AppModuleConfiguration(models.Model):
    app_name = models.CharField(max_length=100, unique=True)
    is_enabled = models.BooleanField(default=True)
    is_core = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default='active')
```

## 🏭 Factory Pattern

### **Service Factory**
```python
# core/factories.py
class ServiceFactory:
    def __init__(self):
        self._services_cache = {}
    
    def create_article_service(self, repository=None):
        """Cria ArticleService com dependências injetadas"""
        if not repository:
            repository = ArticleRepository()
        return ArticleService(repository=repository)
```

### **Uso do Factory**
```python
# Em views ou outros serviços
from core.factories import ServiceFactory

factory = ServiceFactory()
article_service = factory.create_article_service()
articles = article_service.get_all_articles()
```

## 👁️ Observer Pattern

### **Event System**
```python
# core/observers.py
class EventDispatcher:
    def __init__(self):
        self._subscribers = {}
    
    def subscribe(self, event_type, callback):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
    
    def notify(self, event_type, data):
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                callback(data)
```

### **Uso do Observer**
```python
# Em serviços
from core.observers import event_dispatcher

def on_article_created(article):
    # Enviar notificação
    # Atualizar cache
    # Registrar analytics
    pass

event_dispatcher.subscribe('article_created', on_article_created)
```

## 🔗 Repository Pattern

### **Interface Base**
```python
# apps/common/interfaces/base.py
from abc import ABC, abstractmethod
from typing import List, Optional, Any

class IRepository(ABC):
    @abstractmethod
    def get_all(self) -> List[Any]:
        pass
    
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[Any]:
        pass
    
    @abstractmethod
    def create(self, data: dict) -> Any:
        pass
    
    @abstractmethod
    def update(self, obj: Any, data: dict) -> Any:
        pass
    
    @abstractmethod
    def delete(self, obj: Any) -> bool:
        pass
```

### **Implementação**
```python
# apps/articles/repositories/article_repository.py
from apps.common.interfaces.base import IRepository

class ArticleRepository(IRepository):
    def __init__(self):
        self.model = Article
    
    def get_all(self) -> List[Article]:
        return self.model.objects.all()
    
    def get_by_id(self, id: int) -> Optional[Article]:
        try:
            return self.model.objects.get(id=id)
        except self.model.DoesNotExist:
            return None
```

## 🔒 Sistema de Segurança

### **Middleware Stack**
```python
# core/settings.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'axes.middleware.AxesMiddleware',
    'csp.middleware.CSPMiddleware',
    'apps.accounts.middleware.RateLimitMiddleware',
    'apps.accounts.middleware.AccessControlMiddleware',
    'apps.config.middleware.module_middleware.ModuleAccessMiddleware',
]
```

### **Rate Limiting**
```python
# apps/accounts/middleware/rate_limit.py
class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Implementação de rate limiting
        return self.get_response(request)
```

## ⚡ Sistema de Cache

### **Cache Manager**
```python
# core/cache.py
class CacheManager:
    def __init__(self):
        self.backends = {}
        self.default_backend = "django"
    
    def get(self, key: str, backend_name: str = None) -> Optional[Any]:
        backend = self.get_backend(backend_name)
        return backend.get(key)
    
    def set(self, key: str, value: Any, timeout: int = None) -> bool:
        backend = self.get_backend()
        return backend.set(key, value, timeout)
```

### **Cache Decorators**
```python
# Decorator para cache de métodos
@cache_method_result(timeout=300)
def get_popular_articles(self):
    return self.repository.get_popular_articles()
```

## 📊 Monitoramento e Performance

### **Performance Monitor**
```python
# core/performance.py
class PerformanceMonitor:
    def __init__(self):
        self.timers = {}
        self.metrics = []
    
    def start_timer(self, name: str) -> str:
        timer_id = f"{name}_{int(time.time() * 1000000)}"
        self.timers[timer_id] = {
            'name': name,
            'start_time': time.time()
        }
        return timer_id
    
    def stop_timer(self, timer_id: str) -> float:
        if timer_id in self.timers:
            elapsed = time.time() - self.timers[timer_id]['start_time']
            del self.timers[timer_id]
            return elapsed
        return 0.0
```

## 🔄 Fluxo de Dados

### **Request Flow**
```
1. Request → Nginx (Proxy Reverso)
2. Nginx → Gunicorn (WSGI)
3. Gunicorn → Django (WSGI Application)
4. Django → Middleware Stack
5. Middleware → URL Router
6. URL Router → View
7. View → Service Layer
8. Service Layer → Repository Layer
9. Repository Layer → Database
10. Response ← View ← Service ← Repository ← Database
```

### **Event Flow**
```
1. User Action (ex: criar artigo)
2. View recebe request
3. View chama Service
4. Service executa lógica de negócio
5. Service chama Repository
6. Repository salva no Database
7. Service dispara evento via Observer
8. Event handlers executam ações
9. Response retorna para usuário
```

## 🎯 Benefícios da Arquitetura

### **Manutenibilidade**
- Código bem organizado e estruturado
- Responsabilidades claramente definidas
- Fácil localização e correção de bugs

### **Escalabilidade**
- Módulos independentes
- Cache distribuído
- Banco de dados otimizado

### **Testabilidade**
- Injeção de dependências
- Interfaces bem definidas
- Código desacoplado

### **Flexibilidade**
- Módulos habilitáveis/desabilitáveis
- Configurações dinâmicas
- Extensibilidade via plugins

## 🚀 Próximos Passos

### **Melhorias Planejadas**
- [ ] API REST completa
- [ ] Sistema de microserviços
- [ ] Cache distribuído com Redis
- [ ] Monitoramento avançado
- [ ] Sistema de plugins
- [ ] CI/CD pipeline completo

---

**Project Nix** - Arquitetura robusta e escalável ✨ 