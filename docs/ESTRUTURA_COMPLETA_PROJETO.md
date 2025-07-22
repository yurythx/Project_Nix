# 📋 FireFlies CMS - Estrutura Completa do Projeto

## 🎯 Visão Geral
**FireFlies CMS** é um sistema de gerenciamento de conteúdo modular desenvolvido em Django, focado em artigos, páginas e gestão de usuários, com arquitetura baseada em padrões SOLID e design system acessível.

## 🏗️ Arquitetura do Sistema

### Padrões Implementados
- **Factory Pattern**: Criação de objetos complexos
- **Observer Pattern**: Notificações e eventos
- **Repository Pattern**: Abstração de dados
- **Service Layer**: Lógica de negócio
- **Dependency Injection**: Inversão de controle

### Estrutura Modular
```
Project_Nix/
├── apps/                    # Aplicações modulares
│   ├── accounts/           # Sistema de usuários
│   ├── articles/           # Sistema de artigos
│   ├── config/            # Configurações do sistema
│   ├── pages/             # Páginas estáticas
│   └── common/            # Utilitários compartilhados
├── core/                  # Configurações Django
├── static/               # Arquivos estáticos
├── media/                # Uploads de usuários
├── templates/            # Templates globais
├── docs/                 # Documentação
└── scripts/              # Scripts de deploy
```

## 📦 Apps e Funcionalidades

### 1. **accounts** - Sistema de Usuários
**Funcionalidades:**
- Registro e autenticação de usuários
- Perfis com avatars e biografias
- Recuperação de senha
- Sistema de permissões granulares
- Login por email ou username

**Arquivos Principais:**
- `models.py`: User, Profile
- `views.py`: Login, Register, Profile
- `forms.py`: Formulários de autenticação
- `services.py`: Lógica de negócio

### 2. **articles** - Sistema de Artigos
**Funcionalidades:**
- CRUD completo de artigos
- Sistema de categorias e tags
- Comentários com moderação
- Artigos em destaque
- SEO otimizado
- Editor TinyMCE

**Arquivos Principais:**
- `models.py`: Article, Category, Tag, Comment
- `views.py`: ArticleListView, ArticleDetailView
- `services.py`: ArticleService, CommentService
- `repositories.py`: ArticleRepository
- `admin.py`: Interface administrativa

### 3. **config** - Configurações do Sistema
**Funcionalidades:**
- Dashboard administrativo
- Configuração de email SMTP
- Gerenciamento de módulos
- Setup wizard para primeira instalação
- Configurações globais

**Arquivos Principais:**
- `models.py`: SystemConfig, ModuleConfig
- `views.py`: ConfigDashboard, EmailConfig
- `services.py`: ConfigService
- `middleware.py`: SmartRedirectMiddleware

### 4. **pages** - Páginas Estáticas
**Funcionalidades:**
- Criação de páginas estáticas
- Sistema de navegação
- Templates flexíveis
- SEO para páginas

**Arquivos Principais:**
- `models.py`: Page
- `views.py`: PageView, PageListView
- `templates/`: Templates base e includes

### 5. **common** - Utilitários Compartilhados
**Funcionalidades:**
- Mixins reutilizáveis
- Utilitários de validação
- Helpers para templates
- Constantes globais

## 🎨 Design System

### Sistema de Cores (Nova Paleta Roxo Nix)
```css
/* Cores Primárias */
--nix-primary: #1a1d29;          /* Azul escuro profundo */
--nix-accent: #7c3aed;           /* Roxo elegante */
--nix-accent-dark: #5b21b6;      /* Roxo escuro */
--nix-accent-light: #8b5cf6;     /* Roxo claro */
--nix-accent-alt: #6366f1;       /* Índigo complementar */

/* Tema Claro */
--text-color: #0f172a;           /* Contraste 16.8:1 */
--bg-color: #ffffff;
--link-color: #5b21b6;           /* Roxo escuro */

/* Tema Escuro */
--text-color: #f8fafc;           /* Contraste 15.8:1 */
--bg-color: #0f172a;
--link-color: #a855f7;           /* Roxo claro */
```

### Acessibilidade WCAG 2.1 AA
- Todos os contrastes ≥ 4.5:1
- Navegação por teclado completa
- Suporte a leitores de tela
- Responsive design
- Focus management

## 🗄️ Banco de Dados

### Modelos Principais

#### User (accounts)
```python
class User(AbstractUser):
    email = EmailField(unique=True)
    username = CharField(max_length=150, unique=True)
    first_name = CharField(max_length=30)
    last_name = CharField(max_length=30)
```

#### Article (articles)
```python
class Article(models.Model):
    title = CharField(max_length=200)
    slug = SlugField(unique=True)
    content = TextField()
    excerpt = TextField()
    author = ForeignKey(User)
    category = ForeignKey(Category)
    tags = ManyToManyField(Tag)
    featured = BooleanField(default=False)
    published = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

#### Comment (articles)
```python
class Comment(models.Model):
    article = ForeignKey(Article)
    author = ForeignKey(User, null=True, blank=True)
    name = CharField(max_length=100)
    email = EmailField()
    content = TextField()
    parent = ForeignKey('self', null=True, blank=True)
    approved = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
```

#### Page (pages)
```python
class Page(models.Model):
    title = CharField(max_length=200)
    slug = SlugField(unique=True)
    content = TextField()
    template = CharField(max_length=100)
    published = BooleanField(default=True)
    meta_description = CharField(max_length=160)
```

## 🔧 Configurações e Middleware

### Settings Principais
```python
# core/settings.py
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.accounts',
    'apps.articles',
    'apps.config',
    'apps.pages',
    'apps.common',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.config.middleware.SmartRedirectMiddleware',
]
```

### Middleware Customizado
- **SmartRedirectMiddleware**: Redirecionamento inteligente
- **Rate Limiting**: Proteção contra flood
- **Security Headers**: Headers de segurança

## 🎯 URLs e Roteamento

### URLs Principais
```python
# core/urls.py
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('artigos/', include('apps.articles.urls')),
    path('config/', include('apps.config.urls')),
    path('', include('apps.pages.urls')),
]
```

### Padrões de URL
- `/artigos/` - Lista de artigos
- `/artigos/<slug>/` - Detalhe do artigo
- `/accounts/login/` - Login
- `/accounts/register/` - Registro
- `/config/` - Dashboard administrativo

## 📁 Estrutura de Templates

### Templates Base
```
templates/
├── base.html                 # Template principal
├── includes/
│   ├── _head.html           # Meta tags, CSS
│   ├── _nav.html            # Navegação
│   ├── _footer.html         # Rodapé
│   └── _toasts.html         # Notificações
└── admin/
    └── base_site_custom.html # Admin customizado
```

### Sistema de Herança
```django
<!-- base.html -->
<!DOCTYPE html>
<html lang="pt-br">
<head>
    {% include 'includes/_head.html' %}
</head>
<body>
    {% include 'includes/_nav.html' %}
    <main>
        {% block content %}{% endblock %}
    </main>
    {% include 'includes/_footer.html' %}
</body>
</html>
```

## 🎨 Assets e Frontend

### CSS Estruturado
```
static/css/
├── main.css              # Sistema de cores e layout
├── forms.css             # Formulários
├── accessibility.css     # Acessibilidade
└── tinymce-content.css   # Editor de conteúdo
```

### JavaScript Modular
```
static/js/
├── main.js               # Funcionalidades principais
├── theme-toggle.js       # Toggle de tema
├── animations.js         # Animações
├── performance.js        # Otimizações
└── image-optimizer.js    # Otimização de imagens
```

### Recursos Estáticos
- **Bootstrap 5.3.2**: Framework CSS
- **Font Awesome 6.5.1**: Ícones
- **TinyMCE**: Editor WYSIWYG
- **Google Fonts**: Roboto, Fira Mono

## 🧪 Testes

### Estrutura de Testes
```
apps/articles/tests/
├── test_articles_comments.py    # Testes de comentários
├── test_featured_articles.py    # Artigos em destaque
├── test_editor_permissions.py   # Permissões
└── test_toc.py                  # Índice de conteúdo
```

### Cobertura Atual
- **46 testes implementados**
- **45 passando, 1 falhando**
- **Factory Boy** para dados de teste
- **pytest-django** como runner

## 🚀 Deploy e Produção

### Scripts de Deploy
```
scripts/
├── deploy_gcp.sh         # Deploy Google Cloud
├── setup_production.sh   # Configuração produção
└── backup.sh             # Backup automático
```

### Configurações de Produção
- **PostgreSQL**: Banco de dados
- **Redis**: Cache e sessões
- **Nginx**: Servidor web
- **Gunicorn**: WSGI server
- **Google Cloud**: Hospedagem

## 📊 Métricas e Monitoramento

### Performance
- **Lazy loading**: Imagens e conteúdo
- **Cache**: Redis para queries
- **Minificação**: CSS e JS
- **CDN**: Assets estáticos

### Segurança
- **CSRF Protection**: Ativo
- **XSS Protection**: Headers configurados
- **Rate Limiting**: Proteção contra ataques
- **HTTPS**: Forçado em produção

## 🔄 Fluxo de Desenvolvimento

### Git Workflow
1. **Feature branches**: Para novas funcionalidades
2. **Pull requests**: Code review obrigatório
3. **CI/CD**: Testes automatizados
4. **Deploy**: Automático após merge

### Comandos Úteis
```bash
# Desenvolvimento
make install          # Instalar dependências
make migrate          # Executar migrações
make test            # Executar testes
make run             # Iniciar servidor

# Produção
make deploy          # Deploy completo
make backup          # Backup do banco
make logs            # Ver logs
```

## 📚 Documentação Disponível

### Documentos Técnicos
- `ARQUITETURA_ATUAL.md` - Arquitetura detalhada
- `ACESSIBILIDADE.md` - Guia de acessibilidade
- `NOVA_PALETA_ROXO.md` - Sistema de cores
- `README.md` - Guia de instalação

### Guias de Uso
- Setup inicial e configuração
- Criação de artigos e páginas
- Gerenciamento de usuários
- Configuração de email

## 🔍 Exemplos de Código Importantes

### Service Layer Example
```python
# apps/articles/services.py
class ArticleService:
    def __init__(self, repository=None):
        self.repository = repository or ArticleRepository()

    def create_article(self, data, author):
        article = self.repository.create({
            **data,
            'author': author,
            'slug': self._generate_slug(data['title'])
        })
        self._notify_observers('article_created', article)
        return article

    def get_featured_articles(self, limit=5):
        return self.repository.get_featured(limit)
```

### Repository Pattern Example
```python
# apps/articles/repositories.py
class ArticleRepository:
    def get_published(self):
        return Article.objects.filter(published=True)

    def get_by_category(self, category):
        return self.get_published().filter(category=category)

    def get_featured(self, limit=5):
        return self.get_published().filter(featured=True)[:limit]
```

### Factory Pattern Example
```python
# apps/common/factories.py
class ServiceFactory:
    _services = {}

    @classmethod
    def get_service(cls, service_name):
        if service_name not in cls._services:
            cls._services[service_name] = cls._create_service(service_name)
        return cls._services[service_name]
```

## 🛠️ Configurações Específicas

### Email Configuration
```python
# Configuração SMTP dinâmica
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = get_config('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = get_config('EMAIL_PORT', 587)
EMAIL_USE_TLS = get_config('EMAIL_USE_TLS', True)
```

### Cache Configuration
```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

### Security Settings
```python
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
```

---

**Esta estrutura fornece uma visão completa do projeto FireFlies CMS, incluindo arquitetura, funcionalidades, configurações e fluxos de trabalho.**
