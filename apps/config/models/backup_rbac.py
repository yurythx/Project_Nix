from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
import uuid

User = get_user_model()

class BackupRole(models.Model):
    """Funções específicas para backup com princípio de menor privilégio"""
    
    ROLE_LEVELS = [
        ('viewer', 'Backup Viewer'),
        ('operator', 'Backup Operator'),
        ('admin', 'Backup Administrator'),
        ('auditor', 'Backup Auditor'),
        ('compliance_officer', 'Compliance Officer'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    role_level = models.CharField(max_length=20, choices=ROLE_LEVELS)
    
    # Permissões Granulares
    can_view_backups = models.BooleanField(default=True)
    can_create_backups = models.BooleanField(default=False)
    can_restore_backups = models.BooleanField(default=False)
    can_delete_backups = models.BooleanField(default=False)
    can_manage_policies = models.BooleanField(default=False)
    can_view_audit_logs = models.BooleanField(default=False)
    can_access_encrypted_data = models.BooleanField(default=False)
    
    # Restrições por Tipo de Dados
    allowed_data_classifications = models.JSONField(default=list)
    allowed_backup_types = models.JSONField(default=list)
    
    # Separação de Deveres (SoD)
    conflicting_roles = models.ManyToManyField('self', blank=True, symmetrical=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Backup Role'
        verbose_name_plural = 'Backup Roles'

class UserBackupRole(models.Model):
    """Atribuição de funções com controle temporal"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(BackupRole, on_delete=models.CASCADE)
    
    # Controle Temporal
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField(null=True, blank=True)
    
    # Aprovação
    approved_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='approved_role_assignments')
    approval_reason = models.TextField()
    
    # Auditoria
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'User Backup Role'
        verbose_name_plural = 'User Backup Roles'
        unique_together = ['user', 'role']

class BackupAccessRequest(models.Model):
    """Solicitações de acesso com workflow de aprovação"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('denied', 'Denied'),
        ('expired', 'Expired'),
    ]
    
    REQUEST_TYPES = [
        ('restore', 'Restore Request'),
        ('download', 'Download Request'),
        ('delete', 'Delete Request'),
        ('role_assignment', 'Role Assignment Request'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='backup_requests')
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES)
    
    # Detalhes da Solicitação
    backup_id = models.CharField(max_length=255, null=True, blank=True)
    requested_role = models.ForeignKey(BackupRole, on_delete=models.CASCADE, null=True, blank=True)
    justification = models.TextField()
    
    # Aprovação
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approver = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='backup_approvals')
    approval_notes = models.TextField(blank=True)
    
    # Timing
    requested_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Backup Access Request'
        verbose_name_plural = 'Backup Access Requests'
        ordering = ['-requested_at']