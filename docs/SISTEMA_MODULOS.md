# 🧩 Sistema de Módulos - FireFlies CMS

## 📋 Visão Geral

O Sistema de Módulos do FireFlies CMS permite controlar dinamicamente quais funcionalidades estão disponíveis no sistema. Administradores podem habilitar/desabilitar módulos em tempo real, controlando o acesso dos usuários a diferentes partes da aplicação.

## 🎯 Características Principais

### ✅ Funcionalidades Implementadas

- **Controle Dinâmico**: Habilitar/desabilitar módulos sem reiniciar o servidor
- **Módulos Principais**: Proteção automática dos módulos essenciais (accounts, config, pages)
- **Interface Web**: Painel administrativo para gerenciamento de módulos
- **Middleware Inteligente**: Verificação automática de acesso por URL
- **Dependências**: Sistema de dependências entre módulos
- **Permissões**: Controle granular de permissões por módulo
- **Navegação**: Menu dinâmico baseado em módulos ativos
- **Auditoria**: Logs de alterações nos módulos

## 🏗️ Arquitetura do Sistema

### Componentes Principais

#### 1. Modelo de Configuração
```python
# apps/config/models/app_module_config.py
class AppModuleConfiguration(models.Model):
    # Identificação
    app_name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Status e Tipo
    is_enabled = models.BooleanField(default=True)
    is_core = models.BooleanField(default=False)
    module_type = models.CharField(max_length=20, choices=MODULE_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    # Navegação
    menu_icon = models.CharField(max_length=100)
    menu_order = models.PositiveIntegerField(default=100)
    show_in_menu = models.BooleanField(default=True)
    url_pattern = models.CharField(max_length=200, blank=True)
    
    # Dependências e Permissões
    dependencies = models.JSONField(default=list)
    required_permissions = models.JSONField(default=list)
    
    # Configurações Específicas
    module_settings = models.JSONField(default=dict)
    version = models.CharField(max_length=20, blank=True)
```

#### 2. Middleware de Controle
```python
# apps/config/middleware/module_middleware.py
class ModuleAccessMiddleware:
    def __call__(self, request):
        app_name = self.get_app_name_from_url(request.path)
        if app_name and not self.is_module_enabled(app_name):
            raise PermissionDenied("Módulo não disponível")
        return self.get_response(request)

class ModuleContextMiddleware:
    def __call__(self, request):
        # Adiciona contexto dos módulos ao request
        request.enabled_modules = AppModuleConfiguration.get_enabled_modules()
        return self.get_response(request)
```

#### 3. Serviço de Módulos
```python
# apps/config/services/module_service.py
class ModuleService:
    def get_enabled_modules(self):
        return AppModuleConfiguration.get_enabled_modules()
    
    def enable_module(self, app_name):
        module = AppModuleConfiguration.objects.get(app_name=app_name)
        module.is_enabled = True
        module.save()
    
    def disable_module(self, app_name):
        if app_name in AppModuleConfiguration.CORE_APPS:
            raise ValidationError("Não é possível desabilitar módulos principais")
        module = AppModuleConfiguration.objects.get(app_name=app_name)
        module.is_enabled = False
        module.save()
```

## 📊 Tipos de Módulos

### 1. Módulos Principais (Core)
- **accounts**: Sistema de usuários e autenticação
- **config**: Painel administrativo e configurações
- **pages**: Páginas estáticas e navegação

**Características**:
- Não podem ser desabilitados
- Sempre ativos no sistema
- Funcionalidades essenciais

### 2. Módulos de Funcionalidade (Feature)
- **articles**: Sistema de artigos e comentários
- **blog**: Sistema de blog (futuro)
- **shop**: Sistema de e-commerce (futuro)

**Características**:
- Podem ser habilitados/desabilitados
- Funcionalidades opcionais
- Dependências controladas

### 3. Módulos de Integração (Integration)
- **api**: API REST (futuro)
- **notifications**: Sistema de notificações (futuro)
- **analytics**: Analytics e métricas (futuro)

**Características**:
- Integrações externas
- Funcionalidades avançadas
- Dependências complexas

## 🔧 Configuração de Módulos

### Inicialização Automática
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

### Comandos de Gerenciamento
```bash
# Inicializar módulos
python manage.py shell -c "
from apps.config.models.app_module_config import AppModuleConfiguration
AppModuleConfiguration.initialize_core_modules()
"

# Verificar módulos ativos
python manage.py shell -c "
from apps.config.models.app_module_config import AppModuleConfiguration
modules = AppModuleConfiguration.get_enabled_modules()
for module in modules:
    print(f'{module.app_name}: {module.display_name}')
"

# Habilitar módulo
python manage.py shell -c "
from apps.config.models.app_module_config import AppModuleConfiguration
AppModuleConfiguration.objects.filter(app_name='articles').update(is_enabled=True)
"

# Desabilitar módulo
python manage.py shell -c "
from apps.config.models.app_module_config import AppModuleConfiguration
AppModuleConfiguration.objects.filter(app_name='articles').update(is_enabled=False)
"
```

## 🎮 Interface Web

### Painel de Controle
- **URL**: `/config/modulos/`
- **Função**: Gerenciar módulos do sistema
- **Recursos**:
  - Lista de todos os módulos
  - Status de cada módulo
  - Botões para habilitar/desabilitar
  - Informações detalhadas
  - Dependências e permissões

### Funcionalidades da Interface

#### 1. Listagem de Módulos
```html
<!-- apps/config/templates/config/modules/module_list.html -->
<div class="module-grid">
    {% for module in modules %}
    <div class="module-card {% if module.is_enabled %}enabled{% else %}disabled{% endif %}">
        <div class="module-header">
            <i class="{{ module.menu_icon }}"></i>
            <h3>{{ module.display_name }}</h3>
        </div>
        <div class="module-body">
            <p>{{ module.description }}</p>
            <div class="module-status">
                <span class="badge badge-{{ module.status }}">
                    {{ module.get_status_display }}
                </span>
            </div>
        </div>
        <div class="module-actions">
            {% if module.is_enabled %}
                <button class="btn btn-warning" onclick="disableModule('{{ module.app_name }}')">
                    Desabilitar
                </button>
            {% else %}
                <button class="btn btn-success" onclick="enableModule('{{ module.app_name }}')">
                    Habilitar
                </button>
            {% endif %}
        </div>
    </div>
    {% endfor %}
</div>
```

#### 2. Detalhes do Módulo
```html
<!-- apps/config/templates/config/modules/module_detail.html -->
<div class="module-details">
    <h2>{{ module.display_name }}</h2>
    <div class="module-info">
        <p><strong>App:</strong> {{ module.app_name }}</p>
        <p><strong>Tipo:</strong> {{ module.get_module_type_display }}</p>
        <p><strong>Status:</strong> {{ module.get_status_display }}</p>
        <p><strong>Versão:</strong> {{ module.version|default:"N/A" }}</p>
    </div>
    
    <div class="module-dependencies">
        <h4>Dependências</h4>
        <ul>
            {% for dep in module.dependencies %}
            <li>{{ dep }}</li>
            {% empty %}
            <li>Nenhuma dependência</li>
            {% endfor %}
        </ul>
    </div>
    
    <div class="module-permissions">
        <h4>Permissões Necessárias</h4>
        <ul>
            {% for perm in module.required_permissions %}
            <li>{{ perm }}</li>
            {% empty %}
            <li>Nenhuma permissão específica</li>
            {% endfor %}
        </ul>
    </div>
</div>
```

## 🔐 Controle de Acesso

### Middleware de Verificação
```python
# apps/config/middleware/module_middleware.py
class ModuleAccessMiddleware:
    def __call__(self, request):
        # Extrair nome do app da URL
        path = request.path.strip('/')
        app_name = self.get_app_name_from_path(path)
        
        if app_name:
            # Verificar se o módulo está habilitado
            if not self.is_module_enabled(app_name):
                if request.user.is_authenticated:
                    messages.error(request, f"O módulo '{app_name}' não está disponível")
                    return redirect('config:module_list')
                else:
                    raise PermissionDenied("Módulo não disponível")
        
        return self.get_response(request)
    
    def get_app_name_from_path(self, path):
        """Extrai o nome do app da URL"""
        path_parts = path.split('/')
        if path_parts:
            return path_parts[0]
        return None
    
    def is_module_enabled(self, app_name):
        """Verifica se o módulo está habilitado"""
        try:
            module = AppModuleConfiguration.objects.get(app_name=app_name)
            return module.is_enabled and module.status == 'active'
        except AppModuleConfiguration.DoesNotExist:
            return True  # Módulos não configurados são permitidos
```

### Verificação em Views
```python
# apps/config/views/module_views.py
from django.core.exceptions import PermissionDenied

class ModuleListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    def test_func(self):
        # Verificar se o usuário tem permissão para acessar módulos
        return self.request.user.has_perm('config.view_appmoduleconfiguration')
    
    def get_queryset(self):
        return AppModuleConfiguration.objects.all().order_by('menu_order', 'display_name')

class ModuleEnableView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.has_perm('config.change_appmoduleconfiguration')
    
    def post(self, request, app_name):
        try:
            module = AppModuleConfiguration.objects.get(app_name=app_name)
            module.is_enabled = True
            module.save()
            messages.success(request, f"Módulo '{module.display_name}' habilitado")
        except AppModuleConfiguration.DoesNotExist:
            messages.error(request, "Módulo não encontrado")
        
        return redirect('config:module_list')
```

## 📊 Monitoramento e Logs

### Logs de Alterações
```python
# apps/config/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.contenttypes.models import ContentType

@receiver(post_save, sender=AppModuleConfiguration)
def log_module_changes(sender, instance, created, **kwargs):
    """Registra alterações nos módulos"""
    if not created:  # Apenas alterações, não criação
        LogEntry.objects.log_action(
            user_id=getattr(instance, '_current_user_id', None),
            content_type_id=ContentType.objects.get_for_model(instance).pk,
            object_id=instance.pk,
            object_repr=f"Module: {instance.app_name}",
            action_flag=CHANGE,
            change_message=f"Module {instance.app_name} {'enabled' if instance.is_enabled else 'disabled'}"
        )
```

### Métricas de Uso
```python
# apps/config/services/module_service.py
class ModuleService:
    def get_module_stats(self):
        """Retorna estatísticas dos módulos"""
        total_modules = AppModuleConfiguration.objects.count()
        enabled_modules = AppModuleConfiguration.objects.filter(is_enabled=True).count()
        core_modules = AppModuleConfiguration.objects.filter(is_core=True).count()
        feature_modules = AppModuleConfiguration.objects.filter(module_type='feature').count()
        
        return {
            'total': total_modules,
            'enabled': enabled_modules,
            'disabled': total_modules - enabled_modules,
            'core': core_modules,
            'feature': feature_modules,
            'enabled_percentage': (enabled_modules / total_modules * 100) if total_modules > 0 else 0
        }
```

## 🎨 Integração com Templates

### Template Tags Personalizados
```python
# apps/config/templatetags/config_extras.py
from django import template
from apps.config.models.app_module_config import AppModuleConfiguration

register = template.Library()

@register.simple_tag
def get_enabled_modules():
    """Retorna módulos habilitados para o menu"""
    return AppModuleConfiguration.get_enabled_modules().filter(show_in_menu=True)

@register.simple_tag
def is_module_enabled(app_name):
    """Verifica se um módulo específico está habilitado"""
    try:
        module = AppModuleConfiguration.objects.get(app_name=app_name)
        return module.is_enabled and module.status == 'active'
    except AppModuleConfiguration.DoesNotExist:
        return True  # Módulos não configurados são considerados habilitados
```

### Menu Dinâmico
```html
<!-- templates/includes/_navigation.html -->
<nav class="navbar">
    <ul class="nav-menu">
        {% get_enabled_modules as modules %}
        {% for module in modules %}
        <li class="nav-item">
            <a href="{% url module.app_name|add:':index' %}" class="nav-link">
                <i class="{{ module.menu_icon }}"></i>
                {{ module.display_name }}
            </a>
        </li>
        {% endfor %}
    </ul>
</nav>
```

## 🚀 API para Módulos

### Endpoints Disponíveis
```python
# apps/config/views/module_views.py
class ModuleStatsAPIView(APIView):
    """API para estatísticas dos módulos"""
    def get(self, request):
        service = ModuleService()
        stats = service.get_module_stats()
        return Response(stats)

class ModuleDependencyCheckView(APIView):
    """API para verificar dependências de módulos"""
    def get(self, request, app_name):
        try:
            module = AppModuleConfiguration.objects.get(app_name=app_name)
            dependencies = module.dependencies
            missing_deps = []
            
            for dep in dependencies:
                try:
                    dep_module = AppModuleConfiguration.objects.get(app_name=dep)
                    if not dep_module.is_enabled:
                        missing_deps.append(dep)
                except AppModuleConfiguration.DoesNotExist:
                    missing_deps.append(dep)
            
            return Response({
                'module': app_name,
                'dependencies': dependencies,
                'missing_dependencies': missing_deps,
                'can_enable': len(missing_deps) == 0
            })
        except AppModuleConfiguration.DoesNotExist:
            return Response({'error': 'Módulo não encontrado'}, status=404)
```

## 🔍 Troubleshooting

### Problemas Comuns

#### 1. Módulo não aparece no menu
```bash
# Verificar se o módulo está habilitado
python manage.py shell -c "
from apps.config.models.app_module_config import AppModuleConfiguration
module = AppModuleConfiguration.objects.get(app_name='articles')
print(f'Habilitado: {module.is_enabled}')
print(f'Mostrar no menu: {module.show_in_menu}')
print(f'Status: {module.status}')
"
```

#### 2. Erro "Módulo não disponível"
```bash
# Verificar configuração do módulo
python manage.py shell -c "
from apps.config.models.app_module_config import AppModuleConfiguration
module = AppModuleConfiguration.objects.get(app_name='articles')
print(f'App: {module.app_name}')
print(f'Habilitado: {module.is_enabled}')
print(f'Status: {module.status}')
print(f'É core: {module.is_core}')
"
```

#### 3. Dependências não resolvidas
```bash
# Verificar dependências
python manage.py shell -c "
from apps.config.models.app_module_config import AppModuleConfiguration
module = AppModuleConfiguration.objects.get(app_name='articles')
print(f'Dependências: {module.dependencies}')
for dep in module.dependencies:
    try:
        dep_module = AppModuleConfiguration.objects.get(app_name=dep)
        print(f'{dep}: {"Habilitado" if dep_module.is_enabled else "Desabilitado"}')
    except AppModuleConfiguration.DoesNotExist:
        print(f'{dep}: Não encontrado')
"
```

### Comandos de Diagnóstico
```bash
# Listar todos os módulos
python manage.py shell -c "
from apps.config.models.app_module_config import AppModuleConfiguration
for module in AppModuleConfiguration.objects.all():
    print(f'{module.app_name}: {"✓" if module.is_enabled else "✗"} ({module.status})')
"

# Verificar módulos habilitados
python manage.py shell -c "
from apps.config.models.app_module_config import AppModuleConfiguration
enabled = AppModuleConfiguration.get_enabled_modules()
print(f'Total habilitados: {enabled.count()}')
for module in enabled:
    print(f'- {module.app_name}: {module.display_name}')
"

# Reinicializar módulos
python manage.py shell -c "
from apps.config.models.app_module_config import AppModuleConfiguration
AppModuleConfiguration.initialize_core_modules()
print('Módulos reinicializados')
"
```

## 🎯 Próximos Passos

### Melhorias Planejadas

1. **Sistema de Plugins**
   - Instalação dinâmica de módulos
   - Marketplace de módulos
   - Versionamento automático

2. **Dependências Avançadas**
   - Verificação automática de dependências
   - Resolução de conflitos
   - Instalação automática de dependências

3. **Cache de Módulos**
   - Cache de configurações
   - Cache de permissões
   - Invalidação automática

4. **API REST Completa**
   - CRUD completo via API
   - Documentação automática
   - Autenticação JWT

5. **Monitoramento Avançado**
   - Métricas de uso por módulo
   - Performance por módulo
   - Alertas automáticos

---

**FireFlies CMS** - Sistema de módulos dinâmico e flexível ✨ 