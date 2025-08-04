from django.urls import path
from apps.config.views.backup_enterprise_views import (
    BackupDashboardView,
    BackupPolicyListView,
    BackupPolicyCreateView,
    BackupJobListView,
    BackupMonitoringView,
    BackupComplianceReportView,
    BackupRoleManagementView,
    BackupAccessRequestView,
    BackupAuditLogView
)

app_name = 'backup_enterprise'

urlpatterns = [
    # Dashboard
    path('dashboard/', BackupDashboardView.as_view(), name='dashboard'),
    
    # Políticas
    path('policies/', BackupPolicyListView.as_view(), name='policy_list'),
    path('policies/create/', BackupPolicyCreateView.as_view(), name='policy_create'),
    
    # Jobs
    path('jobs/', BackupJobListView.as_view(), name='job_list'),
    
    # Monitoramento
    path('monitoring/', BackupMonitoringView.as_view(), name='monitoring'),
    
    # Compliance
    path('compliance/', BackupComplianceReportView.as_view(), name='compliance_report'),
    
    # RBAC
    path('roles/', BackupRoleManagementView.as_view(), name='role_management'),
    path('access-request/', BackupAccessRequestView.as_view(), name='access_request'),
    
    # Auditoria
    path('audit/', BackupAuditLogView.as_view(), name='audit_log'),
]