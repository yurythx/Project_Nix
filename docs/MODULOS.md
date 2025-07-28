# 🔌 Sistema de Módulos Project Nix

## 📋 Visão Geral

O **Sistema de Módulos** do Project Nix permite controlar dinamicamente quais funcionalidades estão disponíveis no sistema. Administradores podem habilitar/desabilitar módulos através da interface web, controlando o acesso dos usuários a diferentes partes da aplicação.

## 🎯 Características Principais

- **🔧 Controle Dinâmico**: Módulos podem ser habilitados/desabilitados sem reiniciar o servidor
- **🛡️ Proteção de Módulos Core**: Módulos essenciais não podem ser desabilitados
- **🎨 Interface Web**: Painel administrativo para gerenciamento de módulos
- **🔍 Middleware Inteligente**: Verificação automática de permissões de módulos
- **📊 Estatísticas**: Monitoramento de uso e status dos módulos

## 🏗️ Arquitetura do Sistema

### **Componentes Principais**

#### **1. AppModuleConfiguration Model**
```python
# apps/config/models/app_module_config.py
class AppModuleConfiguration(models.Model):
    app_name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_enabled = models.BooleanField(default=True)
    is_core = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default='active')
    module_type = models.CharField(max_length=20, default='feature')
    menu_icon = models.CharField(max_length=100, default='fas fa-puzzle-piece')
    menu_order = models.PositiveIntegerField(default=100)
    show_in_menu = models.BooleanField(default=True)
```

#### **2. ModuleService**
```python
# apps/config/services/module_service.py
class ModuleService(IModuleService):
    def get_enabled_modules(self) -> List[AppModuleConfiguration]:
        return AppModuleConfiguration.get_enabled_modules()
    
    def enable_module(self, app_name: str, user=None) -> bool:
        module = self.get_module_by_name(app_name)
        if module:
            module.is_enabled = True
            module.status = 'active'
            module.save()
            return True
        return False
    
    def disable_module(self, app_name: str, user=None) -> bool:
        if app_name in self.core_apps:
            raise ValidationError("Não é possível desabilitar módulos principais")
        module = self.get_module_by_name(app_name)
        if module:
            module.is_enabled = False
            module.status = 'inactive'
            module.save()
            return True
        return False
```

#### **3. ModuleAccessMiddleware**
```python
# apps/config/middleware/module_middleware.py
class ModuleAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Verifica se o módulo está habilitado
        app_name = self._get_app_name(request)
        if app_name and not self._is_module_enabled(app_name):
            return HttpResponseForbidden("Módulo não disponível")
        
        return self.get_response(request)
```

## 📊 Tipos de Módulos

### **1. Core Modules (Principais)**
Módulos essenciais que **nunca podem ser desabilitados**:

- **`accounts`**: Sistema de usuários e autenticação
- **`config`**: Painel administrativo e configurações
- **`pages`**: Páginas estáticas e navegação

**Características:**
- ✅ Sempre ativos no sistema
- ❌ Não podem ser desabilitados
- 🔧 Funcionalidades essenciais
- 🛡️ Proteção automática

### **2. Feature Modules (Funcionalidades)**
Módulos de funcionalidades que podem ser habilitados/desabilitados:

- **`articles`**: Sistema de artigos e comentários
- **`books`**: Gerenciamento de livros digitais
- **`mangas`**: Sistema de mangás online
- **`audiobooks`**: Sistema de audiolivros

**Características:**
- ✅ Podem ser habilitados/desabilitados
- 🔧 Funcionalidades opcionais
- 📊 Dependências controladas
- 🎨 Interface personalizada

### **3. Integration Modules (Integrações)**
Módulos de integração com sistemas externos:

- **`api`**: API REST (futuro)
- **`notifications`**: Sistema de notificações (futuro)
- **`analytics`**: Analytics e métricas (futuro)

**Características:**
- 🔗 Integrações externas
- ⚡ Funcionalidades avançadas
- 🔧 Dependências complexas
- 📊 Monitoramento especializado

## 🔧 Configuração e Inicialização

### **Inicialização Automática**
```python
# apps/config/models/app_module_config.py
@classmethod
def initialize_core_modules(cls):
    """Inicializa os módulos principais automaticamente"""
    core_modules_data = [
        {
            'app_name': 'accounts',
            'display_name': 'Contas e Usuários',
            'description': 'Sistema de autenticação, registro e gerenciamento de usuários',
            'url_pattern': 'accounts/',
            'menu_icon': 'fas fa-users',
            'menu_order': 10,
        },
        {
            'app_name': 'config',
            'display_name': 'Configurações',
            'description': 'Painel de configurações e administração do sistema',
            'url_pattern': 'config/',
            'menu_icon': 'fas fa-cogs',
            'menu_order': 90,
        },
        {
            'app_name': 'pages',
            'display_name': 'Páginas',
            'description': 'Sistema de páginas estáticas e dinâmicas',
            'url_pattern': '',
            'menu_icon': 'fas fa-file-alt',
            'menu_order': 20,
        },
    ]
    
    for module_data in core_modules_data:
        cls.objects.get_or_create(
            app_name=module_data['app_name'],
            defaults={
                **module_data,
                'module_type': 'core',
                'is_core': True,
                'is_enabled': True,
                'status': 'active',
            }
        )
```

### **Sincronização com Apps Instalados**
```python
# apps/config/services/module_service.py
def sync_with_installed_apps(self, user: User = None) -> Dict:
    """Sincroniza módulos com apps instalados"""
    installed_apps = self.get_installed_apps_list()
    default_active_apps = ['articles', 'books', 'audiobooks', 'mangas']
    
    for app_path in installed_apps:
        app_name = app_path.split('.')[-1]
        is_core = app_name in self.core_apps
        is_default_active = app_name in default_active_apps
        
        module_data = {
            'app_name': app_name,
            'display_name': app_name.title(),
            'description': f'Módulo {app_name}',
            'is_enabled': is_core or is_default_active,
            'is_core': is_core,
            'status': 'active' if (is_core or is_default_active) else 'inactive'
        }
        
        self.create_module(module_data, user)
```

## 🎨 Interface Web

### **Painel de Controle**
Acessível em `/config/modulos/`, o painel permite:

- **📋 Listar Módulos**: Visualizar todos os módulos disponíveis
- **✅ Habilitar/Desabilitar**: Controle de status dos módulos
- **📊 Estatísticas**: Uso e performance dos módulos
- **🔧 Configurações**: Personalizar módulos individuais

### **Menu Dinâmico**
```python
# apps/config/middleware/module_middleware.py
class ModuleContextMiddleware:
    def process_template_response(self, request, response):
        if hasattr(response, 'context_data'):
            # Adiciona módulos ativos ao contexto
            module_service = ModuleService()
            response.context_data['active_modules'] = module_service.get_menu_modules()
        return response
```

### **Template de Menu**
```django
<!-- templates/includes/_nav.html -->
{% for module in active_modules %}
    {% if module.show_in_menu %}
        <li class="nav-item">
            <a class="nav-link" href="{% url module.app_name|add:':index' %}">
                <i class="{{ module.menu_icon }}"></i>
                {{ module.display_name }}
            </a>
        </li>
    {% endif %}
{% endfor %}
```

## 🔍 Middleware de Verificação

### **ModuleAccessMiddleware**
```python
class ModuleAccessMiddleware:
    def __call__(self, request):
        app_name = self._get_app_name(request)
        
        # Verifica se é um módulo core (sempre permitido)
        if app_name in self.core_apps:
            return self.get_response(request)
        
        # Verifica se o módulo está habilitado
        if app_name and not self._is_module_enabled(app_name):
            if request.user.is_staff:
                messages.warning(request, f"O módulo '{app_name}' está desabilitado")
            else:
                return HttpResponseForbidden("Módulo não disponível no momento")
        
        return self.get_response(request)
    
    def _get_app_name(self, request):
        """Extrai o nome do app da URL"""
        path = request.path_info.lstrip('/')
        if path:
            return path.split('/')[0]
        return None
    
    def _is_module_enabled(self, app_name):
        """Verifica se o módulo está habilitado"""
        try:
            module = AppModuleConfiguration.objects.get(app_name=app_name)
            return module.is_enabled and module.status == 'active'
        except AppModuleConfiguration.DoesNotExist:
            return False
```

## 📊 API para Módulos

### **Endpoints Disponíveis**
```python
# apps/config/views/module_views.py
class ModuleListView(ListView):
    model = AppModuleConfiguration
    template_name = 'config/modules/module_list.html'
    context_object_name = 'modules'

class ModuleToggleView(View):
    def post(self, request, app_name):
        action = request.POST.get('action')
        module_service = ModuleService()
        
        if action == 'enable':
            success = module_service.enable_module(app_name, request.user)
        elif action == 'disable':
            success = module_service.disable_module(app_name, request.user)
        
        if success:
            messages.success(request, f"Módulo {app_name} {action}do com sucesso")
        else:
            messages.error(request, f"Erro ao {action}r módulo {app_name}")
        
        return redirect('config:module_list')
```

### **Comandos de Gerenciamento**
```bash
# Ativar módulos principais
python manage.py activate_articles

# Verificar status dos módulos
python manage.py shell -c "
from apps.config.models.app_module_config import AppModuleConfiguration
modules = AppModuleConfiguration.objects.all()
for m in modules:
    print(f'{m.app_name}: {\"✅\" if m.is_enabled else \"❌\"}')
"

# Sincronizar módulos
python manage.py shell -c "
from apps.config.services.module_service import ModuleService
service = ModuleService()
result = service.sync_with_installed_apps()
print(result)
"
```

## 🔧 Troubleshooting

### **Problemas Comuns**

#### **1. Módulo não aparece no menu**
```bash
# Verificar se o módulo está habilitado
python manage.py shell -c "
from apps.config.models.app_module_config import AppModuleConfiguration
module = AppModuleConfiguration.objects.get(app_name='articles')
print(f'Enabled: {module.is_enabled}, Status: {module.status}')
"
```

#### **2. Erro "Módulo não disponível"**
```bash
# Habilitar módulo manualmente
python manage.py shell -c "
from apps.config.models.app_module_config import AppModuleConfiguration
AppModuleConfiguration.objects.filter(app_name='articles').update(is_enabled=True, status='active')
"
```

#### **3. Módulo core sendo desabilitado**
```python
# Verificar se é um módulo core
CORE_APPS = ['accounts', 'config', 'pages']

if app_name in CORE_APPS:
    raise ValidationError("Não é possível desabilitar módulos principais")
```

### **Logs e Debugging**
```python
# Habilitar logs de módulos
LOGGING = {
    'loggers': {
        'apps.config': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    },
}
```

## 🚀 Próximos Passos

### **Melhorias Planejadas**
- [ ] **API REST para módulos**: Endpoints para gerenciamento via API
- [ ] **Dependências entre módulos**: Sistema de dependências automático
- [ ] **Versões de módulos**: Controle de versões e atualizações
- [ ] **Plugins externos**: Sistema de plugins de terceiros
- [ ] **Métricas avançadas**: Analytics de uso dos módulos
- [ ] **Cache de módulos**: Cache para melhor performance

### **Funcionalidades Futuras**
- [ ] **Marketplace de módulos**: Repositório de módulos disponíveis
- [ ] **Instalação automática**: Download e instalação de módulos
- [ ] **Temas por módulo**: Temas específicos para cada módulo
- [ ] **Configurações avançadas**: Configurações granulares por módulo

---

**Project Nix** - Sistema de módulos flexível e poderoso ✨ 