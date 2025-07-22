from django import template
import json
import pprint as pp
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def pprint(value):
    """Pretty print para JSON e dicionários"""
    try:
        if isinstance(value, str):
            # Tentar fazer parse do JSON
            parsed = json.loads(value)
            return json.dumps(parsed, indent=2, ensure_ascii=False)
        elif isinstance(value, dict):
            return json.dumps(value, indent=2, ensure_ascii=False)
        else:
            return pp.pformat(value, indent=2)
    except:
        return str(value)


@register.filter
def get_item(dictionary, key):
    """Obter item de dicionário no template"""
    return dictionary.get(key)


@register.filter
def mul(value, arg):
    """Multiplica o valor pelo argumento"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.simple_tag
def config_status_badge(is_active, is_default=False):
    """Gera badge de status para configurações"""
    badges = []
    
    if is_active:
        badges.append('<span class="badge bg-success">Ativo</span>')
    else:
        badges.append('<span class="badge bg-secondary">Inativo</span>')
    
    if is_default:
        badges.append('<span class="badge bg-warning text-dark"><i class="fas fa-star me-1"></i>Padrão</span>')
    
    return ' '.join(badges)


@register.inclusion_tag('config/includes/test_result_badge.html')
def test_result_badge(last_test_result):
    """Renderiza badge do resultado do teste"""
    return {
        'result': last_test_result,
        'success': last_test_result.get('success', False) if last_test_result else False,
        'message': last_test_result.get('message', '') if last_test_result else ''
    }


@register.filter
def engine_icon(engine):
    """Retorna ícone baseado no engine do banco"""
    icons = {
        'django.db.backends.postgresql': 'fas fa-database text-info',
        'django.db.backends.mysql': 'fas fa-database text-warning',
        'django.db.backends.sqlite3': 'fas fa-file-alt text-secondary',
        'django.db.backends.oracle': 'fas fa-database text-danger',
    }
    return icons.get(engine, 'fas fa-database text-muted')


@register.filter
def connection_string(config):
    """Gera string de conexão para exibição (sem senha)"""
    if hasattr(config, 'engine'):
        # Database config
        if config.engine == 'django.db.backends.sqlite3':
            return f"sqlite:///{config.name_db}"
        elif config.host:
            return f"{config.get_engine_display().lower()}://{config.user}@{config.host}:{config.port}/{config.name_db}"
        else:
            return f"{config.get_engine_display().lower()}://localhost/{config.name_db}"
    else:
        # Email config
        protocol = "smtps" if config.email_use_ssl else "smtp"
        if config.email_use_tls:
            protocol += "+tls"
        return f"{protocol}://{config.email_host}:{config.email_port}"


@register.simple_tag
def config_count_badge(count, label, color="primary"):
    """Gera badge com contador"""
    return f'<span class="badge bg-{color}">{count}</span> {label}'


@register.simple_tag(takes_context=True)
def is_config_section_active(context, section_urls):
    """Verifica se uma seção da sidebar está ativa"""
    request = context.get('request')
    if not request:
        return False

    current_url_name = request.resolver_match.url_name if request.resolver_match else None

    if isinstance(section_urls, str):
        section_urls = [section_urls]

    return current_url_name in section_urls


@register.simple_tag(takes_context=True)
def sidebar_section_class(context, section_urls):
    """Retorna classe CSS para seção da sidebar"""
    is_active = is_config_section_active(context, section_urls)
    return 'sidebar-section-active' if is_active else 'sidebar-section'


@register.inclusion_tag('config/includes/sidebar_item.html', takes_context=True)
def sidebar_item(context, url_name, icon, title, description=""):
    """Renderiza item da sidebar"""
    request = context.get('request')
    is_active = False

    if request and request.resolver_match:
        is_active = request.resolver_match.url_name == url_name

    return {
        'url_name': url_name,
        'icon': icon,
        'title': title,
        'description': description,
        'is_active': is_active,
        'request': request
    }


@register.simple_tag
def get_config_stats():
    """Obtém estatísticas rápidas para a sidebar"""
    from django.contrib.auth import get_user_model
    from apps.config.models import EmailConfiguration, AppModuleConfiguration, DatabaseConfiguration

    User = get_user_model()

    try:
        stats = {
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'email_configs': EmailConfiguration.objects.count(),
            'database_configs': DatabaseConfiguration.objects.count(),
            'active_modules': AppModuleConfiguration.objects.filter(is_enabled=True).count(),
            'total_modules': AppModuleConfiguration.objects.count(),
        }
        return stats
    except Exception:
        return {
            'total_users': 0,
            'active_users': 0,
            'email_configs': 0,
            'database_configs': 0,
            'active_modules': 0,
            'total_modules': 0,
        }


@register.filter
def log_row(log):
    """Transforma um log em uma lista de células HTML seguras para _table.html"""
    return [
        format_html('<span class="text-monospace">{}</span>', log.created_at.strftime('%d/%m/%Y %H:%M:%S')),
        log.user.email,
        log.get_action_display(),
        log.target_user.email if log.target_user else '-',
        mark_safe(log.description[:80]),
        log.ip_address or '-',
    ]


@register.filter
def user_row(user):
    """Transforma um usuário em uma lista de células HTML seguras para _table.html"""
    from django.utils.html import format_html
    return [
        format_html('<span class="text-monospace">{}</span>', user.date_joined.strftime('%d/%m/%Y %H:%M:%S')),
        user.email,
        user.get_full_name() or '-',
        user.username,
        'Ativo' if user.is_active else 'Inativo',
        'Staff' if user.is_staff else 'Usuário',
    ]


@register.filter
def module_row(module):
    """Transforma um módulo em uma lista de células HTML seguras para _table.html"""
    from django.utils.html import format_html
    return [
        module.display_name,
        module.app_name,
        module.get_module_type_display(),
        format_html('<span class="badge {}">{}</span>', 'bg-success' if module.is_enabled else 'bg-secondary', 'Habilitado' if module.is_enabled else 'Desabilitado'),
        module.status,
        module.menu_order,
    ]


@register.filter
def group_row(group):
    """Transforma um grupo em uma lista de células HTML seguras para _table.html"""
    return [
        group.name,
        group.user_set.count(),
        ', '.join([perm.codename for perm in group.permissions.all()]) or '-',
    ]


@register.filter
def permission_row(perm):
    """Transforma uma permissão em uma lista de células HTML seguras para _table.html"""
    return [
        perm.name,
        perm.codename,
        perm.content_type.app_label,
        perm.content_type.model,
    ]


@register.filter
def config_row(config):
    """Transforma um objeto de configuração em uma lista de células HTML seguras para _table.html (exemplo para AppModuleConfiguration)"""
    if hasattr(config, 'display_name'):
        return [
            getattr(config, 'display_name', '-'),
            getattr(config, 'app_name', '-'),
            getattr(config, 'status', '-'),
            getattr(config, 'menu_order', '-'),
        ]
    return [str(config)]


@register.filter
def email_config_row(config):
    """Transforma um EmailConfiguration em uma lista de células HTML seguras para _table.html"""
    return [
        getattr(config, 'display_name', '-'),
        getattr(config, 'email_host', '-'),
        getattr(config, 'default_from_email', '-'),
        getattr(config, 'status', '-'),
    ]


@register.filter
def db_config_row(config):
    """Transforma um DatabaseConfiguration em uma lista de células HTML seguras para _table.html"""
    return [
        getattr(config, 'display_name', '-'),
        getattr(config, 'engine', '-'),
        getattr(config, 'name', '-'),
        getattr(config, 'status', '-'),
    ]


@register.filter
def env_backup_row(backup):
    """Transforma um dict de backup de .env em uma lista de células HTML seguras para _table.html"""
    from django.utils.html import format_html
    import datetime
    return [
        backup.get('name', '-'),
        format_html('{} bytes', backup.get('size', 0)),
        datetime.datetime.fromtimestamp(backup.get('modified', 0)).strftime('%d/%m/%Y %H:%M:%S'),
    ]
