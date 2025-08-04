from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

from apps.config.services.backup_orchestrator import BackupOrchestrator
from apps.config.services.backup_monitoring import BackupMonitoringService
from apps.config.models.backup_governance import BackupPolicy, BackupJob

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def execute_scheduled_backup(self, job_id):
    """Executa backup agendado"""
    try:
        orchestrator = BackupOrchestrator()
        result = orchestrator.execute_backup_job(job_id)
        
        if not result['success']:
            logger.error(f"Backup job {job_id} failed: {result.get('error')}")
            raise Exception(result.get('error', 'Unknown error'))
        
        return result
        
    except Exception as exc:
        logger.error(f"Backup job {job_id} failed with exception: {str(exc)}")
        
        # Retry com backoff exponencial
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        
        # Marca job como falhado após esgotar tentativas
        try:
            job = BackupJob.objects.get(id=job_id)
            job.status = 'failed'
            job.error_message = str(exc)
            job.save()
        except BackupJob.DoesNotExist:
            pass
        
        raise exc

@shared_task
def schedule_policy_backups():
    """Agenda backups baseado em políticas ativas"""
    orchestrator = BackupOrchestrator()
    
    active_policies = BackupPolicy.objects.filter(is_active=True)
    scheduled_count = 0
    
    for policy in active_policies:
        # Verifica se precisa agendar novo backup
        if orchestrator._should_schedule_backup(policy):
            result = orchestrator.schedule_policy_backups(str(policy.id))
            if result['success']:
                scheduled_count += 1
                logger.info(f"Backup scheduled for policy {policy.name}")
            else:
                logger.error(f"Failed to schedule backup for policy {policy.name}: {result['error']}")
    
    return f"Scheduled {scheduled_count} backups"

@shared_task
def backup_health_check():
    """Verifica saúde do sistema de backup"""
    monitoring_service = BackupMonitoringService()
    
    # Verifica saúde geral
    health_report = monitoring_service.check_backup_health()
    
    # Envia alertas se necessário
    if health_report['overall_status'] in ['warning', 'critical']:
        monitoring_service._send_health_alert(health_report)
    
    # Detecta ransomware
    ransomware_check = monitoring_service.detect_ransomware_indicators()
    if ransomware_check['suspicious_activity']:
        monitoring_service._send_security_alert(ransomware_check)
    
    return health_report

@shared_task
def cleanup_old_backups():
    """Remove backups antigos baseado em políticas de retenção"""
    cleaned_count = 0
    
    for policy in BackupPolicy.objects.filter(is_active=True):
        cutoff_date = timezone.now() - timedelta(days=policy.retention_days)
        
        old_jobs = BackupJob.objects.filter(
            policy=policy,
            completed_at__lt=cutoff_date,
            status__in=['completed', 'verified']
        )
        
        for job in old_jobs:
            # Remove arquivos físicos
            orchestrator = BackupOrchestrator()
            orchestrator._cleanup_backup_files(job)
            
            # Marca como deletado
            job.status = 'deleted'
            job.save()
            
            cleaned_count += 1
    
    logger.info(f"Cleaned up {cleaned_count} old backups")
    return f"Cleaned {cleaned_count} backups"

@shared_task
def generate_compliance_reports():
    """Gera relatórios de compliance automaticamente"""
    monitoring_service = BackupMonitoringService()
    
    frameworks = ['gdpr', 'hipaa', 'sox', 'iso27001']
    generated_reports = []
    
    for framework in frameworks:
        try:
            result = monitoring_service.send_compliance_report(framework)
            if result['success']:
                generated_reports.append(framework)
                logger.info(f"Generated {framework} compliance report")
        except Exception as e:
            logger.error(f"Failed to generate {framework} report: {str(e)}")
    
    return f"Generated reports for: {', '.join(generated_reports)}"