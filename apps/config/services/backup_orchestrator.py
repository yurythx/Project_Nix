from celery import Celery
from django.conf import settings
from typing import Dict, List, Any
import logging
import boto3
from datetime import datetime, timedelta

class BackupOrchestrator:
    """Orquestrador central de backup enterprise"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.celery_app = Celery('backup_orchestrator')
        
    def schedule_policy_backups(self, policy_id: str) -> Dict[str, Any]:
        """Agenda backups baseado em políticas"""
        from apps.config.models.backup_governance import BackupPolicy, BackupJob
        
        try:
            policy = BackupPolicy.objects.get(id=policy_id, is_active=True)
            
            # Calcula próxima execução baseada na frequência
            next_execution = self._calculate_next_execution(policy.backup_frequency)
            
            # Cria job de backup
            backup_job = BackupJob.objects.create(
                policy=policy,
                backup_method=self._determine_backup_method(policy),
                source_path=self._get_source_path(policy.policy_type),
                destination_paths=self._get_destination_paths(policy),
                scheduled_at=next_execution,
                triggered_by=policy.created_by
            )
            
            # Agenda execução no Celery
            self._schedule_celery_task(backup_job.id, next_execution)
            
            return {
                'success': True,
                'job_id': str(backup_job.id),
                'scheduled_at': next_execution.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao agendar backup: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def execute_backup_job(self, job_id: str) -> Dict[str, Any]:
        """Executa job de backup com estratégia 3-2-1-1-0"""
        from apps.config.models.backup_governance import BackupJob
        
        try:
            job = BackupJob.objects.get(id=job_id)
            job.status = 'running'
            job.started_at = datetime.now()
            job.save()
            
            # Executa backup em múltiplos destinos
            results = []
            for destination in job.destination_paths:
                result = self._execute_single_backup(job, destination)
                results.append(result)
            
            # Verifica integridade
            integrity_result = self._verify_backup_integrity(job)
            
            # Atualiza status final
            if all(r['success'] for r in results) and integrity_result['success']:
                job.status = 'verified'
                job.integrity_verified = True
            else:
                job.status = 'failed'
                job.error_message = 'Falha na verificação de integridade'
            
            job.completed_at = datetime.now()
            job.save()
            
            # Log de auditoria
            self._create_audit_log('backup_created', job)
            
            return {
                'success': job.status == 'verified',
                'job_id': str(job.id),
                'results': results,
                'integrity_check': integrity_result
            }
            
        except Exception as e:
            self.logger.error(f"Erro na execução do backup: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _execute_single_backup(self, job: 'BackupJob', destination: Dict[str, Any]) -> Dict[str, Any]:
        """Executa backup para um destino específico"""
        
        destination_type = destination.get('type')
        
        if destination_type == 'local':
            return self._backup_to_local(job, destination)
        elif destination_type == 's3':
            return self._backup_to_s3(job, destination)
        elif destination_type == 'azure_blob':
            return self._backup_to_azure(job, destination)
        else:
            raise ValueError(f"Tipo de destino não suportado: {destination_type}")
    
    def _backup_to_s3(self, job: 'BackupJob', destination: Dict[str, Any]) -> Dict[str, Any]:
        """Backup para Amazon S3 com criptografia e imutabilidade"""
        
        s3_client = boto3.client(
            's3',
            aws_access_key_id=destination['access_key'],
            aws_secret_access_key=destination['secret_key'],
            region_name=destination.get('region', 'us-east-1')
        )
        
        try:
            # Upload com criptografia server-side
            response = s3_client.upload_file(
                job.source_path,
                destination['bucket'],
                f"backups/{job.id}/{datetime.now().strftime('%Y%m%d_%H%M%S')}.backup",
                ExtraArgs={
                    'ServerSideEncryption': 'AES256',
                    'ObjectLockMode': 'GOVERNANCE',  # Imutabilidade
                    'ObjectLockRetainUntilDate': datetime.now() + timedelta(days=job.policy.retention_days)
                }
            )
            
            return {
                'success': True,
                'destination': 's3',
                'location': f"s3://{destination['bucket']}/backups/{job.id}/",
                'encrypted': True,
                'immutable': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'destination': 's3',
                'error': str(e)
            }
    
    def _verify_backup_integrity(self, job: 'BackupJob') -> Dict[str, Any]:
        """Verifica integridade do backup (0 erros na estratégia 3-2-1-1-0)"""
        
        import hashlib
        
        try:
            # Calcula checksum do arquivo original
            with open(job.source_path, 'rb') as f:
                original_hash = hashlib.sha256(f.read()).hexdigest()
            
            # Verifica checksums em todos os destinos
            integrity_checks = []
            for destination in job.destination_paths:
                backup_hash = self._get_backup_checksum(job, destination)
                integrity_checks.append({
                    'destination': destination['type'],
                    'original_hash': original_hash,
                    'backup_hash': backup_hash,
                    'match': original_hash == backup_hash
                })
            
            all_match = all(check['match'] for check in integrity_checks)
            
            if all_match:
                job.checksum_value = original_hash
                job.save()
            
            return {
                'success': all_match,
                'checks': integrity_checks,
                'algorithm': 'SHA-256'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }