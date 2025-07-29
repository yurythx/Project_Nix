from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .manga import Manga
from .capitulo import Capitulo
from .offline_download import OfflineDownload

User = get_user_model()

class BatchDownload(models.Model):
    """
    Modelo para downloads em lote de capítulos.
    """
    STATUS_CHOICES = [
        ('pending', _('Pendente')),
        ('processing', _('Processando')),
        ('completed', _('Concluído')),
        ('failed', _('Falhou')),
        ('cancelled', _('Cancelado')),
        ('paused', _('Pausado')),
    ]

    PRIORITY_CHOICES = [
        ('low', _('Baixa')),
        ('normal', _('Normal')),
        ('high', _('Alta')),
        ('urgent', _('Urgente')),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='batch_downloads',
        verbose_name=_('Usuário')
    )
    name = models.CharField(
        _('Nome do Lote'),
        max_length=200,
        help_text=_('Nome descritivo para o lote de downloads')
    )
    description = models.TextField(
        _('Descrição'),
        blank=True
    )
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    priority = models.CharField(
        _('Prioridade'),
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='normal'
    )
    
    # Configurações do lote
    manga = models.ForeignKey(
        Manga,
        on_delete=models.CASCADE,
        related_name='batch_downloads',
        verbose_name=_('Mangá')
    )
    start_chapter = models.PositiveIntegerField(
        _('Capítulo Inicial'),
        null=True,
        blank=True
    )
    end_chapter = models.PositiveIntegerField(
        _('Capítulo Final'),
        null=True,
        blank=True
    )
    volume_filter = models.CharField(
        _('Filtro de Volume'),
        max_length=100,
        blank=True,
        help_text=_('Filtrar por volume específico (ex: "1-5" ou "1,3,5")')
    )
    quality = models.CharField(
        _('Qualidade'),
        max_length=20,
        choices=[
            ('original', _('Original')),
            ('compressed', _('Comprimido')),
            ('web_optimized', _('Otimizado para Web')),
        ],
        default='original'
    )
    
    # Progresso
    total_chapters = models.PositiveIntegerField(
        _('Total de Capítulos'),
        default=0
    )
    completed_chapters = models.PositiveIntegerField(
        _('Capítulos Concluídos'),
        default=0
    )
    failed_chapters = models.PositiveIntegerField(
        _('Capítulos com Falha'),
        default=0
    )
    total_size_mb = models.FloatField(
        _('Tamanho Total (MB)'),
        default=0.0
    )
    downloaded_size_mb = models.FloatField(
        _('Tamanho Baixado (MB)'),
        default=0.0
    )
    
    # Controle
    max_concurrent_downloads = models.PositiveIntegerField(
        _('Downloads Simultâneos Máximos'),
        default=3
    )
    retry_failed = models.BooleanField(
        _('Tentar Novamente Falhas'),
        default=True
    )
    max_retries = models.PositiveIntegerField(
        _('Máximo de Tentativas'),
        default=3
    )
    
    # Resultados
    file_path = models.CharField(
        _('Caminho do Arquivo'),
        max_length=500,
        blank=True,
        help_text=_('Caminho para o arquivo ZIP do lote')
    )
    file_size = models.BigIntegerField(
        _('Tamanho do Arquivo'),
        null=True,
        blank=True
    )
    error_message = models.TextField(
        _('Mensagem de Erro'),
        blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        _('Criado em'),
        auto_now_add=True
    )
    started_at = models.DateTimeField(
        _('Iniciado em'),
        null=True,
        blank=True
    )
    completed_at = models.DateTimeField(
        _('Concluído em'),
        null=True,
        blank=True
    )
    expires_at = models.DateTimeField(
        _('Expira em'),
        null=True,
        blank=True
    )

    class Meta:
        app_label = 'mangas'
        verbose_name = _('Download em Lote')
        verbose_name_plural = _('Downloads em Lote')
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['user', 'status'], name='batch_download_user_status_idx'),
            models.Index(fields=['status', 'priority'], name='batch_download_status_priority_idx'),
            models.Index(fields=['manga', 'created_at'], name='batch_download_manga_date_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.name}"

    @property
    def progress_percentage(self):
        """Retorna a porcentagem de progresso."""
        if self.total_chapters == 0:
            return 0
        return min(100, int((self.completed_chapters / self.total_chapters) * 100))

    @property
    def is_expired(self):
        """Verifica se o download expirou."""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    @property
    def is_available(self):
        """Verifica se o download está disponível."""
        return (
            self.status == 'completed' and 
            not self.is_expired and 
            self.file_path
        )

    def get_file_url(self):
        """Retorna a URL para download do arquivo."""
        if self.is_available:
            from django.core.files.storage import default_storage
            return default_storage.url(self.file_path)
        return None

    def start_processing(self):
        """Inicia o processamento do lote."""
        from django.utils import timezone
        from datetime import timedelta
        
        self.status = 'processing'
        self.started_at = timezone.now()
        self.expires_at = timezone.now() + timedelta(days=30)  # Expira em 30 dias
        self.save()

    def mark_as_completed(self, file_path, file_size):
        """Marca o lote como concluído."""
        from django.utils import timezone
        self.status = 'completed'
        self.file_path = file_path
        self.file_size = file_size
        self.completed_at = timezone.now()
        self.save()

    def mark_as_failed(self, error_message):
        """Marca o lote como falhou."""
        self.status = 'failed'
        self.error_message = error_message
        self.save()

    def cancel(self):
        """Cancela o lote."""
        self.status = 'cancelled'
        self.save()

    def pause(self):
        """Pausa o lote."""
        self.status = 'paused'
        self.save()

    def resume(self):
        """Retoma o lote."""
        if self.status == 'paused':
            self.status = 'processing'
            self.save()

    def get_chapters_to_download(self):
        """Retorna a lista de capítulos para download."""
        chapters = Capitulo.objects.filter(
            manga=self.manga,
            is_published=True
        ).order_by('number')
        
        # Filtrar por volume se especificado
        if self.volume_filter:
            chapters = self._filter_by_volume(chapters)
        
        # Filtrar por range de capítulos
        if self.start_chapter:
            chapters = chapters.filter(number__gte=self.start_chapter)
        if self.end_chapter:
            chapters = chapters.filter(number__lte=self.end_chapter)
        
        return list(chapters)

    def _filter_by_volume(self, chapters):
        """Filtra capítulos por volume."""
        volume_filter = self.volume_filter.strip()
        
        if '-' in volume_filter:
            # Range de volumes (ex: "1-5")
            try:
                start_vol, end_vol = map(int, volume_filter.split('-'))
                return chapters.filter(volume__number__range=[start_vol, end_vol])
            except ValueError:
                return chapters
        elif ',' in volume_filter:
            # Volumes específicos (ex: "1,3,5")
            try:
                volumes = [int(v.strip()) for v in volume_filter.split(',')]
                return chapters.filter(volume__number__in=volumes)
            except ValueError:
                return chapters
        else:
            # Volume único
            try:
                volume_num = int(volume_filter)
                return chapters.filter(volume__number=volume_num)
            except ValueError:
                return chapters

class BatchDownloadItem(models.Model):
    """
    Modelo para itens individuais de um download em lote.
    """
    batch_download = models.ForeignKey(
        BatchDownload,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Download em Lote')
    )
    capitulo = models.ForeignKey(
        Capitulo,
        on_delete=models.CASCADE,
        related_name='batch_download_items',
        verbose_name=_('Capítulo')
    )
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=OfflineDownload.STATUS_CHOICES,
        default='pending'
    )
    priority = models.PositiveIntegerField(
        _('Prioridade'),
        default=0,
        help_text=_('Prioridade do item no lote')
    )
    retry_count = models.PositiveIntegerField(
        _('Tentativas'),
        default=0
    )
    error_message = models.TextField(
        _('Mensagem de Erro'),
        blank=True
    )
    file_path = models.CharField(
        _('Caminho do Arquivo'),
        max_length=500,
        blank=True
    )
    file_size = models.BigIntegerField(
        _('Tamanho do Arquivo'),
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(
        _('Criado em'),
        auto_now_add=True
    )
    completed_at = models.DateTimeField(
        _('Concluído em'),
        null=True,
        blank=True
    )

    class Meta:
        app_label = 'mangas'
        verbose_name = _('Item de Download em Lote')
        verbose_name_plural = _('Itens de Download em Lote')
        ordering = ['priority', 'created_at']
        unique_together = ('batch_download', 'capitulo')
        indexes = [
            models.Index(fields=['batch_download', 'status'], name='batch_item_batch_status_idx'),
            models.Index(fields=['status', 'priority'], name='batch_item_status_priority_idx'),
        ]

    def __str__(self):
        return f"{self.batch_download.name} - Cap. {self.capitulo.number}"

    def mark_as_completed(self, file_path, file_size):
        """Marca o item como concluído."""
        from django.utils import timezone
        self.status = 'completed'
        self.file_path = file_path
        self.file_size = file_size
        self.completed_at = timezone.now()
        self.save()

    def mark_as_failed(self, error_message):
        """Marca o item como falhou."""
        self.status = 'failed'
        self.error_message = error_message
        self.retry_count += 1
        self.save()

    def can_retry(self):
        """Verifica se pode tentar novamente."""
        return (
            self.status == 'failed' and 
            self.retry_count < self.batch_download.max_retries
        )

    def reset_for_retry(self):
        """Reseta o item para nova tentativa."""
        self.status = 'pending'
        self.error_message = ''
        self.save()

class BatchDownloadTemplate(models.Model):
    """
    Modelo para templates de download em lote.
    """
    name = models.CharField(
        _('Nome do Template'),
        max_length=100
    )
    description = models.TextField(
        _('Descrição'),
        blank=True
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='batch_download_templates',
        verbose_name=_('Usuário')
    )
    is_public = models.BooleanField(
        _('Público'),
        default=False,
        help_text=_('Se o template é público para outros usuários')
    )
    
    # Configurações do template
    quality = models.CharField(
        _('Qualidade'),
        max_length=20,
        choices=[
            ('original', _('Original')),
            ('compressed', _('Comprimido')),
            ('web_optimized', _('Otimizado para Web')),
        ],
        default='original'
    )
    max_concurrent_downloads = models.PositiveIntegerField(
        _('Downloads Simultâneos Máximos'),
        default=3
    )
    retry_failed = models.BooleanField(
        _('Tentar Novamente Falhas'),
        default=True
    )
    max_retries = models.PositiveIntegerField(
        _('Máximo de Tentativas'),
        default=3
    )
    
    # Filtros padrão
    default_volume_filter = models.CharField(
        _('Filtro de Volume Padrão'),
        max_length=100,
        blank=True
    )
    include_unpublished = models.BooleanField(
        _('Incluir Não Publicados'),
        default=False
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
        verbose_name = _('Template de Download em Lote')
        verbose_name_plural = _('Templates de Download em Lote')
        ordering = ['name']
        indexes = [
            models.Index(fields=['user', 'is_public'], name='batch_template_user_public_idx'),
        ]

    def __str__(self):
        return self.name

    def create_batch_download(self, manga, name, start_chapter=None, end_chapter=None, volume_filter=None):
        """Cria um novo download em lote baseado no template."""
        return BatchDownload.objects.create(
            user=self.user,
            name=name,
            manga=manga,
            start_chapter=start_chapter,
            end_chapter=end_chapter,
            volume_filter=volume_filter or self.default_volume_filter,
            quality=self.quality,
            max_concurrent_downloads=self.max_concurrent_downloads,
            retry_failed=self.retry_failed,
            max_retries=self.max_retries
        ) 