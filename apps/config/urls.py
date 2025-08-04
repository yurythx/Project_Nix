from django.urls import path
from django.shortcuts import redirect
from apps.config.views import (
    ConfigDashboardView,
    UserListView,
    UserCreateView,
    UserUpdateView,
    UserDeleteView,
    SystemConfigView,
    SetupWizardView,
    SetupAPIView,
    setup_redirect,
    BackupListView,
    BackupDetailView,
    BackupCreateView,
    BackupUpdateView,
    BackupDeleteView,
    BackupDownloadView,
    BackupRestoreView,
    BackupRestoreOptionsView,
)
from apps.config.views.email_views import (
    EmailConfigView,
    EmailTestView,
    email_templates_view,
    email_stats_view,
    test_email_connection_view,
    email_sync_view,
    email_quick_setup_view,
    email_detailed_status_view,
)
from apps.config.views.module_views import (
    ModuleListView,
    ModuleDetailView,
    ModuleUpdateView,
    ModuleStatsAPIView,
    ModuleDependencyCheckView,
    ModuleEnableView,
    ModuleDisableView,
    ModuleTestView,
    ModuleDeleteView
)
from apps.config.views.database_views import (
    DatabaseInfoView,
    DatabaseConnectionTestAjaxView,
)
from apps.config.views.user_views import (
    UserActivateView, UserDeactivateView,
    UserPermissionAssignView, UserPermissionRemoveView,
    UserGroupAssignView, UserGroupRemoveView
)
from apps.config.views.system_config_views import (
    SystemLogListView
)
from apps.config.views.groups import (
    GroupListView, GroupCreateView, GroupUpdateView, GroupDeleteView, GroupDetailView
)
from apps.config.views.backup_views import (
    BackupDatabaseView, BackupMediaView, download_backup,
    DeleteBackupView, RestoreDatabaseView, RestoreMediaView
)
from apps.config.views.permission_dashboard_views import (
    PermissionDashboardView, UserPermissionsView, GroupPermissionsView,
    CacheManagementView, PermissionAnalyticsView, PermissionAPIView
)
from django.urls import path, include

app_name = 'config'

urlpatterns = [
    # Setup Wizard
    path('wizard/', SetupWizardView.as_view(), name='setup_wizard'),
    path('setup/api/', SetupAPIView.as_view(), name='setup_api'),
    path('setup-wizard/api/database-step/', SetupAPIView.as_view(), name='setup_database_api'),
    path('setup-wizard/api/finalize/', SetupAPIView.as_view(), name='setup_finalize_api'),
    path('setup/redirect/', setup_redirect, name='setup_redirect'),
    
    # Dashboard
    path('', ConfigDashboardView.as_view(), name='dashboard'),
    
    # Usuários
    path('usuarios/', UserListView.as_view(), name='user_list'),
    path('usuarios/criar/', UserCreateView.as_view(), name='user_create'),
    path('usuarios/<slug:slug>/editar/', UserUpdateView.as_view(), name='user_update'),
    path('usuarios/<slug:slug>/ativar/', UserActivateView.as_view(), name='user_activate'),
    path('usuarios/<slug:slug>/desativar/', UserDeactivateView.as_view(), name='user_deactivate'),
    path('usuarios/<slug:slug>/deletar/', UserDeleteView.as_view(), name='user_delete'),
    path('users/<slug:slug>/permission/assign/', UserPermissionAssignView.as_view(), name='user_permission_assign'),
    path('users/<slug:slug>/permission/remove/', UserPermissionRemoveView.as_view(), name='user_permission_remove'),
    path('users/<slug:slug>/group/assign/', UserGroupAssignView.as_view(), name='user_group_assign'),
    path('users/<slug:slug>/group/remove/', UserGroupRemoveView.as_view(), name='user_group_remove'),
    
    # Email
    path('email/', EmailConfigView.as_view(), name='email_config'),
    path('email/teste/', EmailTestView.as_view(), name='email_test'),
    path('email/templates/', email_templates_view, name='email_templates'),
    path('email/estatisticas/', email_stats_view, name='email_stats'),
    path('email/sync/', email_sync_view, name='email_sync'),
    path('email/quick-setup/', email_quick_setup_view, name='email_quick_setup'),
    path('email/test-connection/', test_email_connection_view, name='test_email_connection'),
    path('email/detailed-status/', email_detailed_status_view, name='email_detailed_status'),

    # Configurações do Sistema
    path('sistema/', SystemConfigView.as_view(), name='system_config'),
    path('system/logs/', SystemLogListView.as_view(), name='system_logs'),

    # Módulos do Sistema
    path('modules/', ModuleListView.as_view(), name='module_list'),
    path('modules/<str:app_name>/', ModuleDetailView.as_view(), name='module_detail'),
    path('modules/<str:app_name>/update/', ModuleUpdateView.as_view(), name='module_update'),
    path('modules/<str:app_name>/enable/', ModuleEnableView.as_view(), name='module_enable'),
    path('modules/<str:app_name>/disable/', ModuleDisableView.as_view(), name='module_disable'),
    path('modules/<str:app_name>/test/', ModuleTestView.as_view(), name='module_test'),
    path('modules/<str:app_name>/delete/', ModuleDeleteView.as_view(), name='module_delete'),

    # APIs dos Módulos
    path('api/modulos/stats/', ModuleStatsAPIView.as_view(), name='module_stats_api'),
    path('api/modulos/<str:app_name>/dependencies/', ModuleDependencyCheckView.as_view(), name='module_dependency_check'),

    # Banco de Dados
    path('banco-dados/', DatabaseInfoView.as_view(), name='database_info'),
    path('ajax/test-database-connection/', DatabaseConnectionTestAjaxView.as_view(), name='database_connection_test'),

    # Dashboard de Permissões
    path('permissions/dashboard/', PermissionDashboardView.as_view(), name='permission_dashboard'),
    path('permissions/users/', UserPermissionsView.as_view(), name='user_permissions'),
    path('permissions/groups/', GroupPermissionsView.as_view(), name='group_permissions'),
    path('permissions/cache/', CacheManagementView.as_view(), name='cache_management'),
    path('permissions/analytics/', PermissionAnalyticsView.as_view(), name='permission_analytics'),
    path('permissions/api/', PermissionAPIView.as_view(), name='permission_api'),

    # Grupos
    path('groups/', GroupListView.as_view(), name='group_list'),
    path('groups/create/', GroupCreateView.as_view(), name='group_create'),
    path('groups/<slug:slug>/', GroupDetailView.as_view(), name='group_detail'),
    path('groups/<slug:slug>/update/', GroupUpdateView.as_view(), name='group_update'),
    path('groups/<slug:slug>/delete/', GroupDeleteView.as_view(), name='group_delete'),
    
    # Moderação de Comentários
    path('comentarios/', lambda request: redirect('articles:moderate_comments'), name='comment_moderation'),

    # Sistema de Backup Moderno (URLs principais)
    path('backups/', BackupListView.as_view(), name='backup_list'),
    path('backups/restore-options/', BackupRestoreOptionsView.as_view(), name='backup_restore_options'),
    path('backups/create/<str:backup_type>/', BackupCreateView.as_view(), name='backup_create'),
    path('backups/<slug:slug>/', BackupDetailView.as_view(), name='backup_detail'),
    path('backups/<slug:slug>/update/', BackupUpdateView.as_view(), name='backup_update'),
    path('backups/<slug:slug>/delete/', BackupDeleteView.as_view(), name='backup_delete'),
    path('backups/<slug:slug>/download/', BackupDownloadView.as_view(), name='backup_download'),
    path('backups/<slug:slug>/restore/', BackupRestoreView.as_view(), name='backup_restore'),

    # Backup Enterprise
    path('backup/enterprise/', include('apps.config.backup_enterprise_urls')),
]
