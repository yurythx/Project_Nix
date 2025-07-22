# 🏗️ Arquitetura Atual - FireFlies CMS

## 📋 Visão Geral

O FireFlies CMS é um sistema de gerenciamento de conteúdo moderno desenvolvido com Django, seguindo princípios SOLID e padrões de design avançados. O sistema é modular, extensível e preparado para produção.

## 🎯 Princípios Arquiteturais

### 1. Modularidade
- **Apps Django Independentes**: Cada funcionalidade é um app Django separado
- **Módulos Dinâmicos**: Sistema permite habilitar/desabilitar módulos em runtime
- **Baixo Acoplamento**: Apps se comunicam via interfaces e eventos

### 2. SOLID Principles
- **Single Responsibility**: Cada classe tem uma única responsabilidade
- **Open/Closed**: Extensível sem modificar código existente
- **Liskov Substitution**: Interfaces bem definidas
- **Interface Segregation**: Interfaces específicas e focadas
- **Dependency Inversion**: Dependências injetadas via Factory

### 3. Padrões de Design
- **Factory Pattern**: Injeção de dependências
- **Observer Pattern**: Sistema de eventos
- **Repository Pattern**: Acesso a dados
- **Service Layer**: Lógica de negócio
- **Middleware Pattern**: Processamento de requisições

## 🏛️ Estrutura Arquitetural

### Camadas do Sistema

```
┌─────────────────────────────────────┐
│           Presentation Layer        │
│  (Views, Templates, Static Files)  │
├─────────────────────────────────────┤
│           Business Layer            │
│     (Services, Factories)          │
├─────────────────────────────────────┤
│           Data Access Layer        │
│      (Repositories, Models)        │
├─────────────────────────────────────┤
│           Infrastructure Layer      │
│    (Database, Cache, External)     │
└─────────────────────────────────────┘
```

### Componentes Principais

#### 1. Core (Núcleo)
```
core/
├── factories.py          # Factory Pattern para injeção de dependências
├── observers.py          # Observer Pattern para eventos
├── settings.py           # Configurações Django
├── urls.py              # URLs principais
├── wsgi.py              # WSGI application
├── asgi.py              # ASGI application
├── health_check.py      # Health checks
├── security.py          # Configurações de segurança
├── performance.py       # Otimizações de performance
└── cache.py             # Configurações de cache
```

#### 2. Apps (Módulos)
```
apps/
├── accounts/            # Sistema de usuários
├── articles/            # Sistema de conteúdo
├── config/              # Painel administrativo
└── pages/               # Páginas estáticas
```

## 🔧 Implementação dos Padrões

### 1. Factory Pattern (Injeção de Dependências)

```python
# core/factories.py
class ServiceFactory:
    def create_article_service(self):
        repository = ArticleRepository()
        return ArticleService(repository)
    
    def create_user_service(self):
        repository = UserRepository()
        return UserService(repository)

# Uso
from core.factories import service_factory
article_service = service_factory.create_article_service()
```

### 2. Observer Pattern (Eventos)

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

# Uso
from core.observers import event_dispatcher

def on_article_created(article):
    print(f"Novo artigo: {article.title}")

event_dispatcher.subscribe('article_created', on_article_created)
event_dispatcher.notify('article_created', article)
```

### 3. Repository Pattern

```python
# apps/articles/repositories/article_repository.py
class ArticleRepository:
    def get_all(self):
        return Article.objects.all()
    
    def get_by_id(self, id):
        return Article.objects.get(id=id)
    
    def create(self, data):
        return Article.objects.create(**data)
    
    def update(self, article, data):
        for key, value in data.items():
            setattr(article, key, value)
        article.save()
        return article
```

### 4. Service Layer

```python
# apps/articles/services/article_service.py
class ArticleService:
    def __init__(self, repository):
        self.repository = repository
    
    def create_article(self, data):
        article = self.repository.create(data)
        event_dispatcher.notify('article_created', article)
        return article
    
    def get_articles(self, filters=None):
        return self.repository.get_all()
```

## 🧩 Sistema de Módulos

### Estrutura de Módulos

```python
# apps/config/models/app_module_config.py
class AppModuleConfiguration(models.Model):
    app_name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=200)
    is_enabled = models.BooleanField(default=True)
    is_core = models.BooleanField(default=False)
    module_type = models.CharField(max_length=20, choices=MODULE_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    # Navegação
    menu_icon = models.CharField(max_length=100)
    menu_order = models.PositiveIntegerField(default=100)
    show_in_menu = models.BooleanField(default=True)
    
    # Dependências
    dependencies = models.JSONField(default=list)
    required_permissions = models.JSONField(default=list)
```

### Middleware de Controle de Módulos

```python
# apps/config/middleware/module_middleware.py
class ModuleAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Verificar se o módulo está habilitado
        app_name = self.get_app_name_from_url(request.path)
        if app_name and not self.is_module_enabled(app_name):
            raise PermissionDenied("Módulo não disponível")
        
        return self.get_response(request)
```

## 🔐 Sistema de Segurança

### Middleware de Segurança

```python
# apps/accounts/middleware.py
class RateLimitMiddleware:
    def __call__(self, request):
        # Implementar rate limiting
        pass

class AccessControlMiddleware:
    def __call__(self, request):
        # Verificar permissões
        pass

class SmartRedirectMiddleware:
    def __call__(self, request):
        # Redirecionamento inteligente
        pass
```

### Configurações de Segurança

```python
# core/security.py
SECURITY_CONFIG = {
    'RATE_LIMIT': {
        'LOGIN_ATTEMPTS': 5,
        'WINDOW_MINUTES': 15,
    },
    'PASSWORD_POLICY': {
        'MIN_LENGTH': 8,
        'REQUIRE_UPPERCASE': True,
        'REQUIRE_LOWERCASE': True,
        'REQUIRE_NUMBERS': True,
        'REQUIRE_SPECIAL': True,
    },
    'SESSION_SECURITY': {
        'SESSION_COOKIE_AGE': 3600,
        'SESSION_EXPIRE_AT_BROWSER_CLOSE': True,
    }
}
```

## 📊 Monitoramento e Health Checks

### Health Checks Implementados

```python
# core/health_check.py
def health_check(request):
    """Health check completo do sistema"""
    checks = {
        'database': check_database(),
        'cache': check_cache(),
        'static_files': check_static_files(),
        'modules': check_modules(),
    }
    
    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503
    
    return JsonResponse({
        'status': 'healthy' if all_healthy else 'unhealthy',
        'checks': checks,
        'timestamp': timezone.now().isoformat(),
    }, status=status_code)

def readiness_check(request):
    """Verificação de readiness para Kubernetes"""
    return health_check(request)

def liveness_check(request):
    """Verificação de liveness para Kubernetes"""
    return JsonResponse({'status': 'alive'})
```

## 🎨 Sistema de Temas

### Estrutura de Temas

```css
/* static/css/fireflies-theme.css */
:root {
    /* Cores do tema FireFlies */
    --fireflies-green: #00ff41;
    --fireflies-yellow: #ffff00;
    --fireflies-dark: #1a1a1a;
    --fireflies-light: #f5f5f5;
}

/* Tema escuro */
[data-theme="dark"] {
    --bg-primary: var(--fireflies-dark);
    --text-primary: var(--fireflies-light);
    --accent-color: var(--fireflies-green);
}

/* Tema claro */
[data-theme="light"] {
    --bg-primary: var(--fireflies-light);
    --text-primary: var(--fireflies-dark);
    --accent-color: var(--fireflies-yellow);
}
```

## 🚀 Configurações de Performance

### Otimizações Implementadas

```python
# core/performance.py
PERFORMANCE_CONFIG = {
    'CACHE': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'TIMEOUT': 300,
    },
    'DATABASE': {
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'MAX_CONNS': 20,
        }
    },
    'STATIC_FILES': {
        'COMPRESS': True,
        'CACHE': True,
        'CDN': False,
    },
    'TEMPLATES': {
        'CACHE': True,
        'OPTIMIZE': True,
    }
}
```

## 🔄 Fluxo de Dados

### Fluxo de Requisição

```
1. Request → Nginx (Proxy Reverso)
2. Nginx → Gunicorn (WSGI)
3. Gunicorn → Django (WSGI Application)
4. Django → Middleware Stack
   ├── SecurityMiddleware
   ├── SetupMiddleware
   ├── SessionMiddleware
   ├── CommonMiddleware
   ├── CsrfViewMiddleware
   ├── AuthenticationMiddleware
   ├── RateLimitMiddleware
   ├── AccessControlMiddleware
   ├── SmartRedirectMiddleware
   ├── ModuleAccessMiddleware
   └── ModuleContextMiddleware
5. Django → URL Router
6. URL Router → View
7. View → Service Layer
8. Service Layer → Repository Layer
9. Repository Layer → Database
10. Response ← View ← Service ← Repository ← Database
```

### Fluxo de Eventos

```
1. User Action (ex: criar artigo)
2. View recebe request
3. View chama Service
4. Service executa lógica de negócio
5. Service chama Repository
6. Repository salva no Database
7. Service dispara evento via Observer
8. Event handlers executam ações (ex: enviar email, atualizar cache)
9. Response retorna para usuário
```

## 📈 Métricas e Monitoramento

### Métricas Coletadas

```python
# core/performance.py
class PerformanceMonitor:
    def __init__(self):
        self.metrics = {}
    
    def record_request(self, path, method, duration, status_code):
        key = f"{method}:{path}"
        if key not in self.metrics:
            self.metrics[key] = {
                'count': 0,
                'total_duration': 0,
                'avg_duration': 0,
                'status_codes': {}
            }
        
        self.metrics[key]['count'] += 1
        self.metrics[key]['total_duration'] += duration
        self.metrics[key]['avg_duration'] = (
            self.metrics[key]['total_duration'] / self.metrics[key]['count']
        )
        
        status = str(status_code)
        if status not in self.metrics[key]['status_codes']:
            self.metrics[key]['status_codes'][status] = 0
        self.metrics[key]['status_codes'][status] += 1
```

## 🔧 Configurações de Ambiente

### Variáveis de Ambiente Críticas

```bash
# Ambiente
ENVIRONMENT=production
DEBUG=False

# Banco de dados
DB_ENGINE=django.db.backends.postgresql
DB_NAME=fireflies
DB_USER=fireflies_user
DB_PASSWORD=sua_senha_segura
DB_HOST=localhost
DB_PORT=5432

# Segurança
SECRET_KEY=sua_chave_secreta_muito_longa
ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua_senha_de_app

# Cache
REDIS_URL=redis://localhost:6379/1

# Módulos
ACTIVE_MODULES=accounts,config,pages,articles
```

## 🛠️ Comandos de Manutenção

### Comandos Essenciais

```bash
# Verificar saúde do sistema
python manage.py check --deploy

# Verificar módulos
python manage.py shell -c "
from apps.config.models.app_module_config import AppModuleConfiguration
print('Módulos ativos:', AppModuleConfiguration.get_enabled_modules().count())
"

# Backup do banco
pg_dump project_nix > backup_$(date +%Y%m%d_%H%M%S).sql

# Limpar cache
python manage.py clearcache

# Coletar estáticos
python manage.py collectstatic --noinput

# Verificar logs
tail -f /var/log/project-nix/django.log
```

## 🎯 Próximos Passos

### Melhorias Planejadas

1. **API REST Completa**
   - Implementar DRF (Django REST Framework)
   - Documentação automática com Swagger
   - Autenticação JWT

2. **Sistema de Notificações**
   - WebSockets para notificações em tempo real
   - Sistema de templates de email
   - Notificações push

3. **Cache Avançado**
   - Cache de consultas complexas
   - Cache de templates
   - Cache de API responses

4. **Monitoramento Avançado**
   - Integração com Prometheus
   - Grafana dashboards
   - Alertas automáticos

5. **Segurança Avançada**
   - 2FA (Two-Factor Authentication)
   - Audit logs
   - Penetration testing

---

**FireFlies CMS** - Arquitetura moderna e escalável ✨ 