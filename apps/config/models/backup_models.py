from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()

class BackupMetadata(models.Model):
    """Modelo para metadados de backups do sistema"""
    
    BACKUP_TYPES = [
        ('database', 'Banco de Dados'),
        ('media', 'Arquivos de Mídia'),
        ('configuration', 'Configurações'),
        ('full', 'Backup Completo'),
    ]
    
    BACKUP_STATUS = [
        ('created', 'Criado'),
        ('in_progress', 'Em Progresso'),
        ('completed', 'Concluído'),
        ('failed', 'Falhou'),
        ('corrupted', 'Corrompido'),
        ('deleted', 'Deletado'),
    ]
    
    # Campos principais
    slug = models.SlugField(unique=True, max_length=255)
    name = models.CharField(max_length=255, verbose_name='Nome do Backup')
    backup_type = models.CharField(max_length=20, choices=BACKUP_TYPES)
    status = models.CharField(max_length=20, choices=BACKUP_STATUS, default='created')
    
    # Metadados do arquivo
    file_path = models.CharField(max_length=500, verbose_name='Caminho do Arquivo')
    file_size = models.BigIntegerField(verbose_name='Tamanho do Arquivo (bytes)')
    sha256_hash = models.CharField(max_length=64, verbose_name='Hash SHA256')
    
    # Informações de auditoria
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Metadados adicionais
    description = models.TextField(blank=True, verbose_name='Descrição')
    metadata = models.JSONField(default=dict, verbose_name='Metadados Adicionais')
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = f"{self.backup_type}-{timezone.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.get_backup_type_display()})"
    
    class Meta:
        verbose_name = 'Metadados de Backup'
        verbose_name_plural = 'Metadados de Backups'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['backup_type', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['created_by', '-created_at']),
        ]