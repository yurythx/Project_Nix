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
    UserListView, UserCreateView, UserUpdateView, UserDeleteView,
    UserActivateView, UserDeactivateView,
    UserPermissionAssignView, UserPermissionRemoveView,
    UserGroupAssignView, UserGroupRemoveView
)
from apps.config.views.system_config_views import (
    SystemConfigView, SystemLogListView
)
from apps.config.views.groups import (
    GroupListView, GroupCreateView, GroupUpdateView, GroupDeleteView, GroupDetailView
)
from apps.config.views.users import (
    UserListView, UserCreateView, UserUpdateView, UserDeleteView
)
from apps.config.views.backup_views import (
    backup_database, backup_media, restore_database, restore_media, download_backup
)


app_name = 'config'

urlpatterns = [
    # Setup Wizard (primeira instalação)
    path('wizard/', SetupWizardView.as_view(), name='setup_wizard'),
    path('wizard-teste/', SetupWizardView.as_view(), name='setup_wizard_teste'),
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
    
    # Grupos (TODO)
    # path('grupos/', GroupListView.as_view(), name='group_list'),
    # path('grupos/criar/', GroupCreateView.as_view(), name='group_create'),
    # path('grupos/<int:group_id>/', GroupDetailView.as_view(), name='group_detail'),
    # path('grupos/<int:group_id>/editar/', GroupUpdateView.as_view(), name='group_update'),
    # path('grupos/<int:group_id>/deletar/', GroupDeleteView.as_view(), name='group_delete'),
    
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

    # Módulos do Sistema (usando AppModuleConfiguration)
    path('modules/', ModuleListView.as_view(), name='module_list'),
    path('modules/<str:app_name>/', ModuleDetailView.as_view(), name='module_detail'),
    path('modules/<str:app_name>/update/', ModuleUpdateView.as_view(), name='module_update'),
    path('modules/<str:app_name>/enable/', ModuleEnableView.as_view(), name='module_enable'),
    path('modules/<str:app_name>/disable/', ModuleDisableView.as_view(), name='module_disable'),
    path('modules/<str:app_name>/delete/', ModuleDeleteView.as_view(), name='module_delete'),

    # APIs dos Módulos
    path('api/modulos/stats/', ModuleStatsAPIView.as_view(), name='module_stats_api'),
    path('api/modulos/<str:app_name>/dependencies/', ModuleDependencyCheckView.as_view(), name='module_dependency_check'),

    # Banco de Dados (somente informações)
    path('banco-dados/', DatabaseInfoView.as_view(), name='database_info'),
    path('ajax/test-database-connection/', DatabaseConnectionTestAjaxView.as_view(), name='database_connection_test'),

    # Backup & Manutenção (TODO)
    path('backup/', SystemConfigView.as_view(), name='backup_config'),
    path('cache/', SystemConfigView.as_view(), name='cache_management'),
    path('logs/', SystemConfigView.as_view(), name='system_logs'),
    
    # Logs de Auditoria (TODO)
    # path('logs/', AuditLogListView.as_view(), name='audit_log_list'),
    # path('logs/usuario/<int:user_id>/', UserAuditLogView.as_view(), name='user_audit_logs'),
    path('system/logs/', SystemLogListView.as_view(), name='system_logs'),

    # Grupos
    path('groups/', GroupListView.as_view(), name='group_list'),
    path('groups/create/', GroupCreateView.as_view(), name='group_create'),
    path('groups/<slug:slug>/', GroupDetailView.as_view(), name='group_detail'),
    path('groups/<slug:slug>/update/', GroupUpdateView.as_view(), name='group_update'),
    path('groups/<slug:slug>/delete/', GroupDeleteView.as_view(), name='group_delete'),

    # Usuários (rotas alternativas)
    # path('users/', UserListView.as_view(), name='user_list'),
    # path('users/create/', UserCreateView.as_view(), name='user_create'),
    # path('users/<int:pk>/', UserDetailView.as_view(), name='user_detail'),
    # path('users/<int:pk>/update/', UserUpdateView.as_view(), name='user_update'),
    # path('users/<int:pk>/delete/', UserDeleteView.as_view(), name='user_delete'),
    
    # Moderação de Comentários (redireciona para articles)
    path('comentarios/', lambda request: redirect('articles:moderate_comments'), name='comment_moderation'),

    # Backup & Restauração
    path('backup/database/', backup_database, name='backup_database'),
    path('backup/media/', backup_media, name='backup_media'),
    path('restore/database/', restore_database, name='restore_database'),
    path('restore/media/', restore_media, name='restore_media'),
    path('backup/download/<str:backup_type>/<str:filename>/', download_backup, name='download_backup'),
]
