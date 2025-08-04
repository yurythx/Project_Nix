from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
import json

from apps.config.models.backup_governance import BackupPolicy, BackupJob, BackupAuditLog
from apps.config.models.backup_rbac import BackupRole, UserBackupRole, BackupAccessRequest
from apps.config.services.backup_orchestrator import BackupOrchestrator
from apps.config.services.backup_monitoring import BackupMonitoringService

class BackupDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Dashboard executivo de backup enterprise"""
    template_name = 'backup/dashboard.html'
    permission_required = 'config.view_backupmetadata'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Métricas de 24 horas
        last_24h = timezone.now() - timedelta(hours=24)
        context['successful_backups_24h'] = BackupJob.objects.filter(
            status__in=['completed', 'verified'],
            completed_at__gte=last_24h
        ).count()
        
        context['failed_backups_24h'] = BackupJob.objects.filter(
            status='failed',
            created_at__gte=last_24h
        ).count()
        
        # Armazenamento total
        total_size = BackupJob.objects.filter(
            status__in=['completed', 'verified']
        ).aggregate(total=models.Sum('total_size_bytes'))['total'] or 0
        context['total_storage_used'] = self._format_bytes(total_size)
        
        # RTO médio
        context['average_rto'] = self._calculate_average_rto()
        
        # Tendências de backup (30 dias)
        context.update(self._get_backup_trends())
        
        # Distribuição de armazenamento
        context.update(self._get_storage_distribution())
        
        # Status de compliance
        context['compliance_frameworks'] = self._get_compliance_status()
        
        # Atividades recentes
        context['recent_activities'] = self._get_recent_activities()
        
        return context
    
    def _format_bytes(self, bytes_value):
        """Formata bytes em unidades legíveis"""
        if bytes_value == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        i = 0
        while bytes_value >= 1024 and i < len(units) - 1:
            bytes_value /= 1024
            i += 1
        
        return f"{bytes_value:.1f} {units[i]}"
    
    def _calculate_average_rto(self):
        """Calcula RTO médio baseado em restaurações recentes"""
        # Implementar lógica de cálculo de RTO
        return 15  # Placeholder
    
    def _get_backup_trends(self):
        """Obtém dados de tendências de backup"""
        last_30_days = timezone.now() - timedelta(days=30)
        
        # Gerar labels dos últimos 30 dias
        labels = []
        success_data = []
        failed_data = []
        
        for i in range(30):
            date = (timezone.now() - timedelta(days=29-i)).date()
            labels.append(date.strftime('%d/%m'))
            
            success_count = BackupJob.objects.filter(
                status__in=['completed', 'verified'],
                completed_at__date=date
            ).count()
            
            failed_count = BackupJob.objects.filter(
                status='failed',
                created_at__date=date
            ).count()
            
            success_data.append(success_count)
            failed_data.append(failed_count)
        
        return {
            'backup_trends_labels': json.dumps(labels),
            'backup_trends_success': json.dumps(success_data),
            'backup_trends_failed': json.dumps(failed_data)
        }
    
    def _get_storage_distribution(self):
        """Obtém distribuição de armazenamento por tipo"""
        # Implementar lógica de distribuição
        return {
            'storage_labels': json.dumps(['Database', 'Media', 'Configuration', 'Application']),
            'storage_data': json.dumps([45, 30, 15, 10])
        }
    
    def _get_compliance_status(self):
        """Obtém status de compliance por framework"""
        frameworks = [
            {
                'name': 'GDPR',
                'status': 'compliant',
                'last_audit': timezone.now() - timedelta(days=30),
                'next_review': timezone.now() + timedelta(days=60)
            },
            {
                'name': 'HIPAA',
                'status': 'warning',
                'last_audit': timezone.now() - timedelta(days=45),
                'next_review': timezone.now() + timedelta(days=15)
            },
            {
                'name': 'ISO 27001',
                'status': 'compliant',
                'last_audit': timezone.now() - timedelta(days=20),
                'next_review': timezone.now() + timedelta(days=70)
            }
        ]
        return frameworks
    
    def _get_recent_activities(self):
        """Obtém atividades recentes do sistema"""
        activities = BackupAuditLog.objects.select_related('user').order_by('-timestamp')[:10]
        
        formatted_activities = []
        for activity in activities:
            formatted_activities.append({
                'description': self._format_activity_description(activity),
                'user': activity.user.get_full_name() or activity.user.username,
                'timestamp': activity.timestamp,
                'status': 'Sucesso' if activity.success else 'Falha',
                'color': 'green' if activity.success else 'red',
                'icon': self._get_activity_icon(activity.action_type)
            })
        
        return formatted_activities
    
    def _format_activity_description(self, activity):
        """Formata descrição da atividade"""
        action_map = {
            'backup_created': 'Backup criado',
            'backup_restored': 'Backup restaurado',
            'backup_deleted': 'Backup excluído',
            'policy_created': 'Política criada',
            'policy_modified': 'Política modificada'
        }
        return action_map.get(activity.action_type, activity.action_type)
    
    def _get_activity_icon(self, action_type):
        """Retorna ícone SVG para o tipo de atividade"""
        icons = {
            'backup_created': '<path d="M5 13l4 4L19 7"></path>',
            'backup_restored': '<path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>',
            'backup_deleted': '<path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>'
        }
        return icons.get(action_type, '<path d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>')

class BackupPolicyListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Lista de políticas de backup"""
    model = BackupPolicy
    template_name = 'backup/policy_list.html'
    context_object_name = 'policies'
    permission_required = 'config.view_backupmetadata'
    paginate_by = 20
    
    def get_queryset(self):
        return BackupPolicy.objects.filter(is_active=True).order_by('-created_at')

class BackupPolicyCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Criação de política de backup"""
    model = BackupPolicy
    template_name = 'backup/policy_form.html'
    permission_required = 'config.add_backupmetadata'
    fields = [
        'name', 'description', 'policy_type', 'backup_frequency',
        'retention_days', 'primary_storage_type', 'secondary_storage_type',
        'offsite_storage_enabled', 'air_gapped_enabled', 'encryption_enabled',
        'immutable_backup', 'compliance_frameworks', 'data_classification',
        'rto_minutes', 'rpo_minutes'
    ]
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Política de backup criada com sucesso!')
        return super().form_valid(form)

class BackupJobListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Lista de jobs de backup"""
    model = BackupJob
    template_name = 'backup/job_list.html'
    context_object_name = 'jobs'
    permission_required = 'config.view_backupmetadata'
    paginate_by = 50
    
    def get_queryset(self):
        return BackupJob.objects.select_related('policy', 'triggered_by').order_by('-created_at')

class BackupMonitoringView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """View de monitoramento de backup"""
    template_name = 'backup/monitoring.html'
    permission_required = 'config.view_backupmetadata'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        monitoring_service = BackupMonitoringService()
        
        # Verificação de saúde
        context['health_report'] = monitoring_service.check_backup_health()
        
        # Detecção de ransomware
        context['ransomware_check'] = monitoring_service.detect_ransomware_indicators()
        
        return context

class BackupComplianceReportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """View para relatórios de compliance"""
    template_name = 'backup/compliance_report.html'
    permission_required = 'config.view_backupmetadata'
    
    def post(self, request, *args, **kwargs):
        framework = request.POST.get('framework')
        
        if framework:
            monitoring_service = BackupMonitoringService()
            result = monitoring_service.send_compliance_report(framework)
            
            if result['success']:
                messages.success(request, f'Relatório de {framework} gerado com sucesso!')
            else:
                messages.error(request, f'Erro ao gerar relatório: {result["error"]}')
        
        return redirect('backup:compliance_report')

class BackupRoleManagementView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Gerenciamento de funções de backup"""
    model = BackupRole
    template_name = 'backup/role_management.html'
    context_object_name = 'roles'
    permission_required = 'config.change_backupmetadata'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_roles'] = UserBackupRole.objects.select_related('user', 'role').filter(is_active=True)
        context['access_requests'] = BackupAccessRequest.objects.filter(status='pending').order_by('-requested_at')
        return context

class BackupAccessRequestView(LoginRequiredMixin, CreateView):
    """Solicitação de acesso a backup"""
    model = BackupAccessRequest
    template_name = 'backup/access_request.html'
    fields = ['request_type', 'backup_id', 'requested_role', 'justification']
    
    def form_valid(self, form):
        form.instance.requester = self.request.user
        messages.success(self.request, 'Solicitação de acesso enviada para aprovação!')
        return super().form_valid(form)

class BackupAuditLogView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Log de auditoria de backup"""
    model = BackupAuditLog
    template_name = 'backup/audit_log.html'
    context_object_name = 'audit_logs'
    permission_required = 'config.view_backupmetadata'
    paginate_by = 100
    
    def get_queryset(self):
        return BackupAuditLog.objects.select_related('user').order_by('-timestamp')