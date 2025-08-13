from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from .manga import Manga
from .capitulo import Capitulo

User = get_user_model()

class ReadingProgress(models.Model):
    """
    Modelo para rastrear o progresso de leitura dos usuários.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reading_progress',
        verbose_name=_('Usuário')
    )
    manga = models.ForeignKey(
        Manga,
        on_delete=models.CASCADE,
        related_name='reading_progress',
        verbose_name=_('Mangá')
    )
    capitulo = models.ForeignKey(
        Capitulo,
        on_delete=models.CASCADE,
        related_name='reading_progress',
        verbose_name=_('Capítulo')
    )
    current_page = models.PositiveIntegerField(
        _('Página Atual'),
        default=1,
        help_text=_('Página atual onde o usuário parou')
    )
    total_pages = models.PositiveIntegerField(
        _('Total de Páginas'),
        help_text=_('Total de páginas do capítulo')
    )
    is_completed = models.BooleanField(
        _('Concluído'),
        default=False,
        help_text=_('Se o capítulo foi completamente lido')
    )
    last_read_at = models.DateTimeField(
        _('Última Leitura'),
        auto_now=True,
        help_text=_('Data e hora da última leitura')
    )
    reading_time = models.PositiveIntegerField(
        _('Tempo de Leitura (segundos)'),
        default=0,
        help_text=_('Tempo total gasto lendo este capítulo')
    )

    class Meta:
        app_label = 'mangas'
        verbose_name = _('Progresso de Leitura')
        verbose_name_plural = _('Progressos de Leitura')
        unique_together = ('user', 'manga', 'capitulo')
        ordering = ['-last_read_at']
        indexes = [
            models.Index(fields=['user', 'manga'], name='rp_user_manga_idx'),
            models.Index(fields=['user', 'last_read_at'], name='rp_user_date_idx'),
            models.Index(fields=['manga', 'capitulo'], name='rp_manga_chapter_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.manga.title} - Cap. {self.capitulo.number}"

    @property
    def progress_percentage(self):
        """Retorna a porcentagem de progresso da leitura."""
        if self.total_pages == 0:
            return 0
        return min(100, int((self.current_page / self.total_pages) * 100))

    def mark_as_completed(self):
        """Marca o capítulo como completamente lido."""
        self.is_completed = True
        self.current_page = self.total_pages
        self.save()

    def update_progress(self, page_number, reading_time_seconds=0):
        """Atualiza o progresso de leitura."""
        self.current_page = min(page_number, self.total_pages)
        self.reading_time += reading_time_seconds
        
        if self.current_page >= self.total_pages:
            self.is_completed = True
            
        self.save()

class ReadingHistory(models.Model):
    """
    Modelo para histórico detalhado de leitura.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reading_history',
        verbose_name=_('Usuário')
    )
    manga = models.ForeignKey(
        Manga,
        on_delete=models.CASCADE,
        related_name='reading_history',
        verbose_name=_('Mangá')
    )
    capitulo = models.ForeignKey(
        Capitulo,
        on_delete=models.CASCADE,
        related_name='reading_history',
        verbose_name=_('Capítulo')
    )
    started_at = models.DateTimeField(
        _('Iniciado em'),
        auto_now_add=True
    )
    completed_at = models.DateTimeField(
        _('Concluído em'),
        null=True,
        blank=True
    )
    session_duration = models.PositiveIntegerField(
        _('Duração da Sessão (segundos)'),
        default=0
    )

    class Meta:
        app_label = 'mangas'
        verbose_name = _('Histórico de Leitura')
        verbose_name_plural = _('Históricos de Leitura')
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', 'started_at'], name='reading_history_user_date_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.manga.title} - Cap. {self.capitulo.number}"

    def mark_completed(self, duration_seconds=0):
        """Marca a sessão como concluída."""
        from django.utils import timezone
        self.completed_at = timezone.now()
        self.session_duration = duration_seconds
        self.save()