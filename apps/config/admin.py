from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from apps.config.models import SystemConfiguration, UserActivityLog, DatabaseConfiguration, AppModuleConfiguration
from apps.config.models.user_activity_log import UserActivityLog

User = get_user_model()

@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    """Admin para configurações do sistema"""
    list_display = ('key', 'description', 'is_active', 'updated_by', 'updated_at')
    list_filter = ('is_active', 'updated_at', 'created_at')
    search_fields = ('key', 'description', 'value')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('key',)

    fieldsets = (
        (None, {
            'fields': ('key', 'value', 'description', 'is_active')
        }),
        ('Metadados', {
            'fields': ('updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        """Salva o modelo definindo o usuário que fez a alteração"""
        if not change or not obj.updated_by:
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    """Admin para logs de atividade"""
    list_display = ('user', 'action', 'timestamp', 'details')
    readonly_fields = ('user', 'action', 'timestamp', 'details')
    ordering = ('-timestamp',)
    list_filter = ('user', 'action', 'timestamp')
    search_fields = ('user__email', 'action', 'details')
    fieldsets = (
        (None, {
            'fields': ('user', 'action', 'timestamp', 'details')
        }),
    )

    def has_add_permission(self, request):
        """Não permite adicionar logs manualmente"""
        return False

    def has_change_permission(self, request, obj=None):
        """Não permite editar logs"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Permite deletar logs apenas para superusuários"""
        return request.user.is_superuser


@admin.register(DatabaseConfiguration)
class DatabaseConfigurationAdmin(admin.ModelAdmin):
    """Admin para configurações de banco de dados"""

    list_display = (
        'name', 'get_engine_display', 'name_db', 'host', 'port',
        'is_default', 'is_active', 'connection_status', 'updated_at'
    )

    list_filter = (
        'engine', 'is_default', 'is_active', 'created_at', 'updated_at'
    )

    search_fields = ('name', 'description', 'name_db', 'host', 'user')

    readonly_fields = (
        'created_at', 'updated_at', 'connection_status'
    )

    ordering = ('-is_default', '-is_active', 'name')

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'description', 'is_default', 'is_active')
        }),
        ('Configurações do Banco', {
            'fields': ('engine', 'name_db', 'host', 'port', 'user', 'password')
        }),
        ('Configurações Avançadas', {
            'fields': ('options',),
            'classes': ('collapse',)
        }),
        ('Status da Conexão', {
            'fields': ('connection_status',),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['test_connections', 'activate_configuration', 'update_env_files']

    def get_engine_display(self, obj):
        """Exibe o tipo de banco com ícone"""
        icons = {
            'django.db.backends.sqlite3': '🗃️',
            'django.db.backends.postgresql': '🐘',
            'django.db.backends.mysql': '🐬',
            'django.db.backends.oracle': '🔶',
        }
        icon = icons.get(obj.engine, '💾')
        return format_html('{} {}', icon, obj.get_engine_display())
    get_engine_display.short_description = 'Tipo de Banco'

    def connection_status(self, obj):
        """Exibe status da conexão com cores"""
        if obj.last_test_date:
            if obj.last_test_result and 'sucesso' in obj.last_test_result.lower():
                return format_html(
                    '<span style="color: green;">✅ Conectado</span>'
                )
            else:
                return format_html(
                    '<span style="color: red;">❌ Erro</span>'
                )
        return format_html('<span style="color: orange;">⚠️ Não testado</span>')
    connection_status.short_description = 'Status da Conexão'

    def save_model(self, request, obj, form, change):
        """Salva o modelo definindo o usuário que fez a alteração"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def test_connections(self, request, queryset):
        """Action para testar conexões selecionadas"""
        success_count = 0
        error_count = 0

        for config in queryset:
            success, message = config.test_connection()
            config.save()  # Salvar resultado do teste

            if success:
                success_count += 1
            else:
                error_count += 1

        if success_count > 0:
            self.message_user(
                request,
                f'{success_count} configuração(ões) testada(s) com sucesso.'
            )

        if error_count > 0:
            self.message_user(
                request,
                f'{error_count} configuração(ões) com erro de conexão.',
                level='ERROR'
            )

    test_connections.short_description = 'Testar conexões selecionadas'

    def activate_configuration(self, request, queryset):
        """Action para ativar configuração selecionada"""
        if queryset.count() != 1:
            self.message_user(
                request,
                'Selecione apenas uma configuração para ativar.',
                level='ERROR'
            )
            return

        config = queryset.first()
        success, message = config.activate_configuration()

        if success:
            self.message_user(request, f'Configuração "{config.name}" ativada com sucesso.')
        else:
            self.message_user(request, f'Erro ao ativar configuração: {message}', level='ERROR')

    activate_configuration.short_description = 'Ativar configuração selecionada'

    def update_env_files(self, request, queryset):
        """Action para atualizar arquivos .env"""
        success_count = 0
        error_count = 0

        for config in queryset:
            success, message = config.update_env_file()

            if success:
                success_count += 1
            else:
                error_count += 1

        if success_count > 0:
            self.message_user(
                request,
                f'{success_count} arquivo(s) .env atualizado(s) com sucesso.'
            )

        if error_count > 0:
            self.message_user(
                request,
                f'{error_count} erro(s) ao atualizar arquivo(s) .env.',
                level='ERROR'
            )

    update_env_files.short_description = 'Atualizar arquivos .env'


# Customização do UserAdmin para incluir campos do modelo personalizado
class CustomUserAdmin(BaseUserAdmin):
    """Admin customizado para o modelo User"""

    # Adiciona campos personalizados às listas
    list_display = BaseUserAdmin.list_display + ('is_verified',)
    list_filter = BaseUserAdmin.list_filter + ('is_verified',)

    # Adiciona campos personalizados aos fieldsets
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Campos Personalizados', {
            'fields': ('is_verified', 'slug'),
        }),
    )

    # Adiciona campos personalizados ao formulário de criação
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Campos Personalizados', {
            'fields': ('email', 'is_verified'),
        }),
    )

# Re-registra o modelo User com o admin customizado
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(AppModuleConfiguration)
class AppModuleConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        'display_name', 'app_name', 'module_type', 'status', 'is_enabled', 'is_core', 'menu_order', 'show_in_menu'
    )
    list_filter = ('module_type', 'status', 'is_enabled', 'is_core', 'show_in_menu')
    search_fields = ('display_name', 'app_name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    ordering = ('menu_order', 'display_name')
    fieldsets = (
        (None, {
            'fields': (
                'display_name', 'app_name', 'description', 'module_type', 'status', 'is_enabled', 'is_core',
                'url_pattern', 'menu_icon', 'menu_order', 'show_in_menu',
                'dependencies', 'required_permissions', 'module_settings',
                'version', 'author', 'documentation_url'
            )
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
