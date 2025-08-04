from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    SystemConfiguration, 
    UserActivityLog, 
    BackupRole,
    UserBackupRole, 
    BackupAccessRequest,
    BackupAuditLog
)

# Configuração do Sistema
@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'description', 'is_active', 'updated_at')
    list_filter = ('is_active', 'updated_at')
    search_fields = ('key', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Configuração', {
            'fields': ('key', 'value', 'description')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

# Log de Atividades
@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('user__username', 'action')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

# Administração de Backup - Funções
@admin.register(BackupRole)
class BackupRoleAdmin(admin.ModelAdmin):
    """Admin para funções de backup"""
    list_display = ('name', 'role_level', 'is_active', 'created_at')
    list_filter = ('role_level', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('role_level', 'name')

@admin.register(UserBackupRole)
class UserBackupRoleAdmin(admin.ModelAdmin):
    """Admin para atribuição de funções"""
    list_display = (
        'user', 'role', 'approved_by', 'valid_from', 'valid_until', 'is_active'
    )
    list_filter = ('role', 'is_active', 'valid_from', 'valid_until')
    search_fields = ('user__username', 'role__name')
    ordering = ('-created_at',)

@admin.register(BackupAccessRequest)
class BackupAccessRequestAdmin(admin.ModelAdmin):
    """Admin para solicitações de acesso"""
    list_display = (
        'requester', 'request_type', 'requested_role', 'status',
        'requested_at', 'approver'
    )
    list_filter = ('request_type', 'status', 'requested_at')
    search_fields = ('requester__username', 'justification')
    ordering = ('-requested_at',)
    fieldsets = (
        ('Solicitação', {
            'fields': ('requester', 'request_type', 'requested_role', 'justification')
        }),
        ('Aprovação', {
            'fields': ('status', 'approver', 'approval_notes')
        }),
        ('Timing', {
            'fields': ('requested_at', 'approved_at', 'expires_at')
        }),
    )

@admin.register(BackupAuditLog)
class BackupAuditLogAdmin(admin.ModelAdmin):
    """Admin para logs de auditoria"""
    list_display = (
        'user', 'action_type', 'resource_type', 'resource_id',
        'success', 'timestamp'
    )
    list_filter = ('action_type', 'resource_type', 'success', 'timestamp')
    search_fields = ('user__username', 'resource_id', 'details')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

# Configurações do Admin Site
admin.site.site_header = "Project Nix - Administração"
admin.site.site_title = "Project Nix Admin"
admin.site.index_title = "Painel de Administração"