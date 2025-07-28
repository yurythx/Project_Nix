# 🔒 Segurança Project Nix

## 📋 Visão Geral

O **Project Nix** implementa um sistema de segurança robusto e abrangente, seguindo as melhores práticas de segurança web e protegendo contra as principais vulnerabilidades conhecidas.

## 🎯 Características de Segurança

- **🛡️ Proteção CSRF**: Tokens CSRF em todos os formulários
- **🔐 Autenticação Segura**: Sistema de login com rate limiting
- **🚫 Rate Limiting**: Proteção contra ataques de força bruta
- **📝 Headers de Segurança**: Headers HTTP de segurança configurados
- **🔍 Validação de Dados**: Validação rigorosa de entrada de dados
- **🛡️ XSS Protection**: Proteção contra Cross-Site Scripting
- **🔒 Controle de Acesso**: Sistema granular de permissões

## 🏗️ Arquitetura de Segurança

### **Middleware Stack de Segurança**
```python
# core/settings.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',      # Headers de segurança
    'corsheaders.middleware.CorsMiddleware',              # CORS
    'django.contrib.sessions.middleware.SessionMiddleware', # Sessões
    'django.middleware.common.CommonMiddleware',          # Middleware comum
    'django.middleware.csrf.CsrfViewMiddleware',          # Proteção CSRF
    'django.contrib.auth.middleware.AuthenticationMiddleware', # Autenticação
    'django.contrib.messages.middleware.MessageMiddleware', # Mensagens
    'django.middleware.clickjacking.XFrameOptionsMiddleware', # Clickjacking
    'axes.middleware.AxesMiddleware',                     # Rate limiting
    'csp.middleware.CSPMiddleware',                       # Content Security Policy
    'apps.accounts.middleware.RateLimitMiddleware',       # Rate limiting customizado
    'apps.accounts.middleware.AccessControlMiddleware',   # Controle de acesso
    'apps.config.middleware.module_middleware.ModuleAccessMiddleware', # Módulos
]
```

## 🔐 Autenticação e Autorização

### **Sistema de Usuários**
```python
# apps/accounts/models/user.py
class User(AbstractUser):
    email = models.EmailField(unique=True)
    is_verified = models.BooleanField(default=False)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
```

### **Backends de Autenticação**
```python
# apps/accounts/backends/email_or_username.py
class EmailOrUsernameModelBackend:
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get('username')
        if username is None or password is None:
            return None
        
        # Tenta autenticar por email ou username
        try:
            user = User.objects.get(
                Q(username=username) | Q(email=username)
            )
        except User.DoesNotExist:
            return None
        
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
```

### **Controle de Acesso**
```python
# apps/accounts/middleware/access_control.py
class AccessControlMiddleware:
    def __call__(self, request):
        # Verifica se o usuário está bloqueado
        if request.user.is_authenticated and request.user.locked_until:
            if timezone.now() < request.user.locked_until:
                return HttpResponseForbidden("Conta temporariamente bloqueada")
            else:
                # Desbloqueia a conta
                request.user.locked_until = None
                request.user.failed_login_attempts = 0
                request.user.save()
        
        return self.get_response(request)
```

## 🚫 Rate Limiting

### **Configuração do Django Axes**
```python
# core/settings.py
AXES_ENABLED = not DEBUG
AXES_FAILURE_LIMIT = 5  # Número de tentativas antes do bloqueio
AXES_COOLOFF_TIME = 1   # 1 hora de bloqueio
AXES_LOCKOUT_TEMPLATE = 'account/lockout.html'
AXES_LOCKOUT_URL = '/accounts/lockout/'
AXES_VERBOSE = True
AXES_LOCK_OUT_BY_COMBINATION_USER_AND_IP = True
```

### **Rate Limiting Customizado**
```python
# apps/accounts/middleware/rate_limit.py
class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limits = {
            'login': {'limit': 5, 'window': 300},  # 5 tentativas por 5 minutos
            'register': {'limit': 3, 'window': 3600},  # 3 registros por hora
            'password_reset': {'limit': 3, 'window': 3600},  # 3 resets por hora
        }
    
    def __call__(self, request):
        # Implementação de rate limiting por IP e ação
        client_ip = self._get_client_ip(request)
        action = self._get_action(request)
        
        if action and not self._is_allowed(client_ip, action):
            return HttpResponseTooManyRequests("Rate limit exceeded")
        
        return self.get_response(request)
```

## 🛡️ Proteção CSRF

### **Configuração CSRF**
```python
# core/settings.py
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_AGE = 31449600  # 1 ano
CSRF_USE_SESSIONS = False
CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://localhost:8000',
    'https://yourdomain.com',
]
```

### **Uso em Templates**
```django
<!-- templates/forms/login.html -->
<form method="post">
    {% csrf_token %}
    <input type="email" name="email" required>
    <input type="password" name="password" required>
    <button type="submit">Login</button>
</form>
```

### **Uso em JavaScript**
```javascript
// static/js/api.js
function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

async function makeAuthenticatedRequest(url, data) {
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),
        },
        body: JSON.stringify(data),
    });
    return response.json();
}
```

## 📝 Headers de Segurança

### **Configuração de Headers**
```python
# core/settings.py
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
X_CONTENT_TYPE_OPTIONS = 'nosniff'
X_XSS_PROTECTION = '1; mode=block'
```

### **Content Security Policy (CSP)**
```python
# core/settings.py
CSP_DEFAULT_SRC = ("'self'",)
CSP_BASE_URI = ("'self'",)
CSP_CONNECT_SRC = ("'self'",)
CSP_FONT_SRC = (
    "'self'",
    "https://fonts.gstatic.com",
    "https://cdnjs.cloudflare.com"
)
CSP_FORM_ACTION = ("'self'",)
CSP_IMG_SRC = (
    "'self'",
    "data:",
    "*"
)
CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-inline'",
    "'unsafe-eval'",
    "https://cdn.jsdelivr.net"
)
CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",
    "https://cdn.jsdelivr.net",
    "https://fonts.googleapis.com",
    "https://cdnjs.cloudflare.com"
)
```

## 🔍 Validação de Dados

### **Validação de Formulários**
```python
# apps/accounts/forms/authentication.py
class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email',
            'autocomplete': 'email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Senha',
            'autocomplete': 'current-password'
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email não encontrado")
        return email
```

### **Validação de Modelos**
```python
# apps/articles/models/article.py
class Article(models.Model):
    title = models.CharField(
        max_length=200,
        validators=[MinLengthValidator(5)],
        help_text='Título do artigo'
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        help_text='URL amigável do artigo'
    )
    
    def clean(self):
        super().clean()
        if self.title and len(self.title.strip()) < 5:
            raise ValidationError("Título deve ter pelo menos 5 caracteres")
```

## 🔐 Sessões e Cookies

### **Configuração de Sessões**
```python
# core/settings.py
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 86400  # 24 horas
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = False
```

### **Configuração de Cookies**
```python
# core/settings.py
# Cookies seguros em produção
if ENVIRONMENT == 'production':
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 ano
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
```

## 🛡️ Proteção contra Ataques

### **SQL Injection**
```python
# Uso seguro de ORM (proteção automática)
# ❌ Ruim - Vulnerável a SQL Injection
articles = Article.objects.raw(f"SELECT * FROM articles WHERE title = '{title}'")

# ✅ Bom - Protegido pelo ORM
articles = Article.objects.filter(title=title)
```

### **XSS Protection**
```python
# Templates Django (escape automático)
# ✅ Bom - Escape automático
{{ user_input }}

# Para conteúdo HTML seguro
{{ user_input|safe }}

# Para conteúdo markdown
{{ user_input|markdown }}
```

### **File Upload Security**
```python
# apps/articles/models/article.py
def validate_file_extension(value):
    import os
    from django.core.exceptions import ValidationError
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Tipo de arquivo não suportado.')

class Article(models.Model):
    featured_image = models.ImageField(
        upload_to='articles/images/',
        validators=[validate_file_extension],
        blank=True,
        help_text='Imagem principal do artigo'
    )
```

## 🔍 Logs de Segurança

### **Configuração de Logs**
```python
# core/settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'security_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.security': {
            'handlers': ['security_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.accounts': {
            'handlers': ['security_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### **Logs de Segurança**
```python
# apps/accounts/views/authentication.py
import logging

logger = logging.getLogger(__name__)

class LoginView(View):
    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            logger.info(f"Login bem-sucedido: {email} - IP: {request.META.get('REMOTE_ADDR')}")
            return redirect('pages:home')
        else:
            logger.warning(f"Tentativa de login falhou: {email} - IP: {request.META.get('REMOTE_ADDR')}")
            messages.error(request, 'Credenciais inválidas')
            return redirect('accounts:login')
```

## 🚀 Configurações de Produção

### **Configurações de Segurança para Produção**
```python
# core/production.py
DEBUG = False
ENVIRONMENT = 'production'

# Configurações de segurança para produção
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 ano
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Cookies seguros
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Configurações de CSRF para produção
CSRF_TRUSTED_ORIGINS = [
    'https://yourdomain.com',
    'https://www.yourdomain.com',
]
```

## 🔧 Comandos de Segurança

### **Verificação de Segurança**
```bash
# Verificar configurações de segurança
python manage.py check --deploy

# Verificar vulnerabilidades conhecidas
python manage.py check --tag security

# Verificar configurações de banco de dados
python manage.py check --database default
```

### **Auditoria de Segurança**
```bash
# Listar usuários com permissões especiais
python manage.py shell -c "
from apps.accounts.models import User
admins = User.objects.filter(is_superuser=True)
for admin in admins:
    print(f'Admin: {admin.email} - Último login: {admin.last_login}')
"

# Verificar tentativas de login falhadas
python manage.py shell -c "
from apps.accounts.models import User
locked_users = User.objects.filter(locked_until__isnull=False)
for user in locked_users:
    print(f'Usuário bloqueado: {user.email} - Bloqueado até: {user.locked_until}')
"
```

## 🚨 Incidentes de Segurança

### **Procedimentos de Emergência**

#### **1. Comprometimento de Conta**
```bash
# Bloquear usuário imediatamente
python manage.py shell -c "
from apps.accounts.models import User
from django.utils import timezone
from datetime import timedelta

user = User.objects.get(email='usuario@exemplo.com')
user.locked_until = timezone.now() + timedelta(hours=24)
user.save()
print(f'Usuário {user.email} bloqueado por 24 horas')
"
```

#### **2. Reset de Senhas em Massa**
```bash
# Forçar reset de senhas
python manage.py shell -c "
from apps.accounts.models import User
from django.contrib.auth.tokens import default_token_generator

users = User.objects.filter(is_active=True)
for user in users:
    token = default_token_generator.make_token(user)
    # Enviar email com token
    print(f'Token para {user.email}: {token}')
"
```

#### **3. Auditoria de Logs**
```bash
# Verificar logs de segurança
tail -f logs/security.log | grep -E "(login|failed|blocked)"

# Verificar tentativas de acesso suspeitas
grep -E "failed.*login" logs/security.log | tail -20
```

## 🚀 Próximos Passos

### **Melhorias de Segurança Planejadas**
- [ ] **Autenticação de Dois Fatores (2FA)**: Implementar TOTP
- [ ] **OAuth2/OpenID Connect**: Integração com provedores externos
- [ ] **Auditoria Completa**: Logs detalhados de todas as ações
- [ ] **Detecção de Anomalias**: Machine learning para detectar comportamentos suspeitos
- [ ] **Backup Criptografado**: Backup seguro dos dados
- [ ] **Penetration Testing**: Testes de penetração regulares

### **Monitoramento Avançado**
- [ ] **Sentry Integration**: Monitoramento de erros e vulnerabilidades
- [ ] **Security Headers Monitoring**: Verificação contínua de headers
- [ ] **SSL Certificate Monitoring**: Monitoramento de certificados
- [ ] **Rate Limiting Analytics**: Análise de padrões de uso

---

**Project Nix** - Segurança robusta e confiável ✨ 