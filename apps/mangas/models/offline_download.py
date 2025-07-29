from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
import zipfile
import tempfile
from .capitulo import Capitulo

User = get_user_model()

class OfflineDownload(models.Model):
    """
    Modelo para gerenciar downloads offline de capítulos.
    """
    STATUS_CHOICES = [
        ('pending', _('Pendente')),
        ('downloading', _('Baixando')),
        ('completed', _('Concluído')),
        ('failed', _('Falhou')),
        ('cancelled', _('Cancelado')),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='offline_downloads',
        verbose_name=_('Usuário')
    )
    capitulo = models.ForeignKey(
        Capitulo,
        on_delete=models.CASCADE,
        related_name='offline_downloads',
        verbose_name=_('Capítulo')
    )
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    file_path = models.CharField(
        _('Caminho do Arquivo'),
        max_length=500,
        blank=True,
        help_text=_('Caminho para o arquivo ZIP do download')
    )
    file_size = models.BigIntegerField(
        _('Tamanho do Arquivo'),
        null=True,
        blank=True,
        help_text=_('Tamanho do arquivo em bytes')
    )
    download_progress = models.PositiveIntegerField(
        _('Progresso do Download'),
        default=0,
        help_text=_('Progresso em porcentagem (0-100)')
    )
    error_message = models.TextField(
        _('Mensagem de Erro'),
        blank=True,
        help_text=_('Mensagem de erro em caso de falha')
    )
    expires_at = models.DateTimeField(
        _('Expira em'),
        null=True,
        blank=True,
        help_text=_('Data de expiração do download')
    )
    created_at = models.DateTimeField(
        _('Criado em'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('Atualizado em'),
        auto_now=True
    )
    completed_at = models.DateTimeField(
        _('Concluído em'),
        null=True,
        blank=True
    )

    class Meta:
        app_label = 'mangas'
        verbose_name = _('Download Offline')
        verbose_name_plural = _('Downloads Offline')
        unique_together = ('user', 'capitulo')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status'], name='download_user_status_idx'),
            models.Index(fields=['status', 'created_at'], name='download_status_date_idx'),
            models.Index(fields=['expires_at'], name='download_expires_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.capitulo.manga.title} Cap. {self.capitulo.number}"

    @property
    def is_expired(self):
        """Verifica se o download expirou."""
        from django.utils import timezone
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    @property
    def is_available(self):
        """Verifica se o download está disponível."""
        return (
            self.status == 'completed' and 
            not self.is_expired and 
            self.file_path and 
            default_storage.exists(self.file_path)
        )

    def get_file_url(self):
        """Retorna a URL para download do arquivo."""
        if self.is_available:
            return default_storage.url(self.file_path)
        return None

    def mark_as_completed(self, file_path, file_size):
        """Marca o download como concluído."""
        from django.utils import timezone
        from datetime import timedelta
        
        self.status = 'completed'
        self.file_path = file_path
        self.file_size = file_size
        self.download_progress = 100
        self.completed_at = timezone.now()
        # Expira em 7 dias
        self.expires_at = timezone.now() + timedelta(days=7)
        self.save()

    def mark_as_failed(self, error_message):
        """Marca o download como falhou."""
        from django.utils import timezone
        self.status = 'failed'
        self.error_message = error_message
        self.save()

    def cancel_download(self):
        """Cancela o download."""
        self.status = 'cancelled'
        # Remove arquivo se existir
        if self.file_path and default_storage.exists(self.file_path):
            default_storage.delete(self.file_path)
        self.save()

    def cleanup_file(self):
        """Remove o arquivo do storage."""
        if self.file_path and default_storage.exists(self.file_path):
            default_storage.delete(self.file_path)
            self.file_path = ''
            self.save(update_fields=['file_path'])

class DownloadQueue(models.Model):
    """
    Modelo para fila de downloads (para downloads em lote).
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='download_queues',
        verbose_name=_('Usuário')
    )
    name = models.CharField(
        _('Nome da Fila'),
        max_length=100,
        help_text=_('Nome descritivo para a fila de downloads')
    )
    is_active = models.BooleanField(
        _('Ativa'),
        default=True,
        help_text=_('Se a fila está ativa')
    )
    max_concurrent_downloads = models.PositiveIntegerField(
        _('Downloads Simultâneos Máximos'),
        default=3,
        help_text=_('Número máximo de downloads simultâneos')
    )
    created_at = models.DateTimeField(
        _('Criado em'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('Atualizado em'),
        auto_now=True
    )

    class Meta:
        app_label = 'mangas'
        verbose_name = _('Fila de Download')
        verbose_name_plural = _('Filas de Download')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.name}"

    @property
    def pending_downloads(self):
        """Retorna downloads pendentes na fila."""
        return self.offline_downloads.filter(status='pending')

    @property
    def active_downloads(self):
        """Retorna downloads ativos na fila."""
        return self.offline_downloads.filter(status='downloading')

    @property
    def completed_downloads(self):
        """Retorna downloads concluídos na fila."""
        return self.offline_downloads.filter(status='completed')

class DownloadPreferences(models.Model):
    """
    Modelo para preferências de download do usuário.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='download_preferences',
        verbose_name=_('Usuário')
    )
    auto_download_new_chapters = models.BooleanField(
        _('Download Automático de Novos Capítulos'),
        default=False,
        help_text=_('Baixar automaticamente novos capítulos de mangás favoritos')
    )
    download_quality = models.CharField(
        _('Qualidade do Download'),
        max_length=20,
        choices=[
            ('original', _('Original')),
            ('compressed', _('Comprimido')),
            ('web_optimized', _('Otimizado para Web')),
        ],
        default='original'
    )
    max_storage_size = models.BigIntegerField(
        _('Tamanho Máximo de Armazenamento (MB)'),
        default=1024,  # 1GB
        help_text=_('Tamanho máximo em MB para downloads offline')
    )
    download_location = models.CharField(
        _('Local de Download'),
        max_length=200,
        default='downloads/',
        help_text=_('Pasta onde os downloads serão salvos')
    )
    keep_downloads_for_days = models.PositiveIntegerField(
        _('Manter Downloads por (Dias)'),
        default=30,
        help_text=_('Número de dias para manter downloads')
    )
    notify_on_completion = models.BooleanField(
        _('Notificar ao Concluir'),
        default=True,
        help_text=_('Enviar notificação quando download for concluído')
    )
    created_at = models.DateTimeField(
        _('Criado em'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('Atualizado em'),
        auto_now=True
    )

    class Meta:
        app_label = 'mangas'
        verbose_name = _('Preferência de Download')
        verbose_name_plural = _('Preferências de Download')

    def __str__(self):
        return f"Preferências de {self.user.username}"

    @property
    def current_storage_usage(self):
        """Retorna o uso atual de armazenamento em MB."""
        total_size = self.user.offline_downloads.filter(
            status='completed'
        ).aggregate(
            total=models.Sum('file_size')
        )['total'] or 0
        return total_size / (1024 * 1024)  # Convert to MB

    @property
    def storage_usage_percentage(self):
        """Retorna a porcentagem de uso do armazenamento."""
        if self.max_storage_size == 0:
            return 0
        return (self.current_storage_usage / self.max_storage_size) * 100

    def can_download(self, estimated_size_mb):
        """Verifica se pode baixar um arquivo do tamanho estimado."""
        return (self.current_storage_usage + estimated_size_mb) <= self.max_storage_size 