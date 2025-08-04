from django.core.mail import send_mail
from django.conf import settings
from typing import Dict, List, Any
import logging
from datetime import datetime, timedelta

class BackupMonitoringService:
    """Serviço de monitoramento proativo de backup"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def check_backup_health(self) -> Dict[str, Any]:
        """Verifica saúde geral do sistema de backup"""
        from apps.config.models.backup_governance import BackupJob, BackupPolicy
        
        health_report = {
            'overall_status': 'healthy',
            'checks': [],
            'alerts': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # Verifica jobs falhados nas últimas 24h
        failed_jobs = BackupJob.objects.filter(
            status='failed',
            created_at__gte=datetime.now() - timedelta(hours=24)
        ).count()
        
        if failed_jobs > 0:
            health_report['checks'].append({
                'name': 'Failed Jobs (24h)',
                'status': 'warning' if failed_jobs < 5 else 'critical',
                'value': failed_jobs,
                'threshold': 5
            })
            
            if failed_jobs >= 5:
                health_report['overall_status'] = 'critical'
                health_report['alerts'].append({
                    'type': 'critical',
                    'message': f'{failed_jobs} backup jobs falharam nas últimas 24 horas',
                    'action_required': True
                })
        
        # Verifica políticas sem backup recente
        stale_policies = self._check_stale_policies()
        if stale_policies:
            health_report['checks'].append({
                'name': 'Stale Policies',
                'status': 'warning',
                'value': len(stale_policies),
                'details': stale_policies
            })
        
        # Verifica espaço de armazenamento
        storage_check = self._check_storage_capacity()
        health_report['checks'].append(storage_check)
        
        # Verifica integridade dos backups
        integrity_check = self._check_backup_integrity()
        health_report['checks'].append(integrity_check)
        
        return health_report
    
    def _check_stale_policies(self) -> List[Dict[str, Any]]:
        """Identifica políticas que não executaram backup recentemente"""
        from apps.config.models.backup_governance import BackupPolicy, BackupJob
        
        stale_policies = []
        
        for policy in BackupPolicy.objects.filter(is_active=True):
            # Calcula quando deveria ter executado o último backup
            expected_interval = self._get_policy_interval_hours(policy.backup_frequency)
            cutoff_time = datetime.now() - timedelta(hours=expected_interval * 2)
            
            recent_jobs = BackupJob.objects.filter(
                policy=policy,
                status__in=['completed', 'verified'],
                completed_at__gte=cutoff_time
            ).exists()
            
            if not recent_jobs:
                stale_policies.append({
                    'policy_id': str(policy.id),
                    'policy_name': policy.name,
                    'frequency': policy.backup_frequency,
                    'last_successful': self._get_last_successful_backup(policy)
                })
        
        return stale_policies
    
    def send_compliance_report(self, framework: str) -> Dict[str, Any]:
        """Gera e envia relatório de compliance"""
        from apps.config.models.backup_governance import BackupAuditLog, BackupJob
        
        try:
            # Coleta métricas de compliance
            report_data = {
                'framework': framework,
                'period': 'last_30_days',
                'generated_at': datetime.now().isoformat(),
                'metrics': {}
            }
            
            # Métricas específicas por framework
            if framework == 'gdpr':
                report_data['metrics'] = self._generate_gdpr_metrics()
            elif framework == 'hipaa':
                report_data['metrics'] = self._generate_hipaa_metrics()
            elif framework == 'sox':
                report_data['metrics'] = self._generate_sox_metrics()
            
            # Gera relatório em PDF
            pdf_path = self._generate_pdf_report(report_data)
            
            # Envia por email para compliance officers
            self._send_compliance_email(framework, pdf_path)
            
            return {
                'success': True,
                'report_path': pdf_path,
                'framework': framework
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar relatório de compliance: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def detect_ransomware_indicators(self) -> Dict[str, Any]:
        """Detecta indicadores de ransomware nos backups"""
        from apps.config.models.backup_governance import BackupJob
        
        indicators = {
            'suspicious_activity': False,
            'alerts': [],
            'recommendations': []
        }
        
        # Verifica padrões suspeitos
        recent_jobs = BackupJob.objects.filter(
            created_at__gte=datetime.now() - timedelta(hours=24)
        )
        
        # Múltiplas falhas consecutivas
        consecutive_failures = 0
        for job in recent_jobs.order_by('-created_at'):
            if job.status == 'failed':
                consecutive_failures += 1
            else:
                break
        
        if consecutive_failures >= 3:
            indicators['suspicious_activity'] = True
            indicators['alerts'].append({
                'type': 'ransomware_indicator',
                'severity': 'high',
                'message': f'{consecutive_failures} falhas consecutivas de backup detectadas',
                'recommendation': 'Verificar integridade do sistema e possível infecção por ransomware'
            })
        
        # Mudanças súbitas no tamanho dos backups
        size_anomalies = self._detect_size_anomalies(recent_jobs)
        if size_anomalies:
            indicators['suspicious_activity'] = True
            indicators['alerts'].extend(size_anomalies)
        
        return indicators