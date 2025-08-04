from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

User = get_user_model()

class BackupPolicy(models.Model):
    """Políticas de backup enterprise com governança"""
    
    POLICY_TYPES = [
        ('database', 'Database'),
        ('media', 'Media Files'),
        ('configuration', 'Configuration'),
        ('application', 'Application Data'),
        ('full_system', 'Full System'),
    ]
    
    FREQUENCY_CHOICES = [
        ('real_time', 'Real Time (CDC)'),
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    COMPLIANCE_FRAMEWORKS = [
        ('gdpr', 'GDPR'),
        ('hipaa', 'HIPAA'),
        ('sox', 'SOX'),
        ('iso27001', 'ISO 27001'),
        ('nist', 'NIST SP 800-34'),
        ('pci_dss', 'PCI DSS'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()
    policy_type = models.CharField(max_length=20, choices=POLICY_TYPES)
    
    # Configurações de Frequência
    backup_frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    retention_days = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    
    # Configurações de Armazenamento (3-2-1-1-0)
    primary_storage_type = models.CharField(max_length=50, default='local_disk')
    secondary_storage_type = models.CharField(max_length=50, default='cloud_s3')
    offsite_storage_enabled = models.BooleanField(default=True)
    air_gapped_enabled = models.BooleanField(default=True)
    
    # Configurações de Segurança
    encryption_enabled = models.BooleanField(default=True)
    encryption_algorithm = models.CharField(max_length=20, default='AES-256')
    immutable_backup = models.BooleanField(default=True)
    
    # Compliance e Governança
    compliance_frameworks = models.JSONField(default=list)
    data_classification = models.CharField(max_length=20, choices=[
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted'),
    ], default='internal')
    
    # RTO/RPO Objectives
    rto_minutes = models.PositiveIntegerField(help_text="Recovery Time Objective in minutes")
    rpo_minutes = models.PositiveIntegerField(help_text="Recovery Point Objective in minutes")
    
    # Auditoria
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_policies')
    approved_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='approved_policies', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Backup Policy'
        verbose_name_plural = 'Backup Policies'
        ordering = ['-created_at']

class BackupJob(models.Model):
    """Jobs de backup com rastreamento completo"""
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('verifying', 'Verifying Integrity'),
        ('verified', 'Verified'),
    ]
    
    BACKUP_METHODS = [
        ('full', 'Full Backup'),
        ('incremental', 'Incremental'),
        ('differential', 'Differential'),
        ('snapshot', 'Snapshot'),
        ('continuous', 'Continuous Data Protection'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    policy = models.ForeignKey(BackupPolicy, on_delete=models.PROTECT)
    
    # Configurações do Job
    backup_method = models.CharField(max_length=20, choices=BACKUP_METHODS)
    source_path = models.TextField()
    destination_paths = models.JSONField(default=list)  # Múltiplos destinos para 3-2-1
    
    # Status e Timing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    scheduled_at = models.DateTimeField()
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Métricas
    total_size_bytes = models.BigIntegerField(null=True, blank=True)
    compressed_size_bytes = models.BigIntegerField(null=True, blank=True)
    transfer_rate_mbps = models.FloatField(null=True, blank=True)
    
    # Verificação de Integridade
    checksum_algorithm = models.CharField(max_length=20, default='SHA-256')
    checksum_value = models.CharField(max_length=128, null=True, blank=True)
    integrity_verified = models.BooleanField(default=False)
    
    # Logs e Erros
    log_output = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    
    # Auditoria
    triggered_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Backup Job'
        verbose_name_plural = 'Backup Jobs'
        ordering = ['-created_at']

class BackupAuditLog(models.Model):
    """Log de auditoria completo para compliance"""
    
    ACTION_TYPES = [
        ('backup_created', 'Backup Created'),
        ('backup_restored', 'Backup Restored'),
        ('backup_deleted', 'Backup Deleted'),
        ('policy_created', 'Policy Created'),
        ('policy_modified', 'Policy Modified'),
        ('access_granted', 'Access Granted'),
        ('access_denied', 'Access Denied'),
        ('integrity_check', 'Integrity Check'),
        ('retention_cleanup', 'Retention Cleanup'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action_type = models.CharField(max_length=30, choices=ACTION_TYPES)
    resource_type = models.CharField(max_length=50)
    resource_id = models.CharField(max_length=255)
    
    # Detalhes da Ação
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    
    # Contexto
    details = models.JSONField(default=dict)
    before_state = models.JSONField(null=True, blank=True)
    after_state = models.JSONField(null=True, blank=True)
    
    # Resultado
    success = models.BooleanField()
    error_message = models.TextField(blank=True)
    
    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['action_type', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]