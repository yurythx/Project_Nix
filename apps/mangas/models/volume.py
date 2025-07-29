from django.db import models
from django.utils.translation import gettext_lazy as _
from .base import SlugMixin, TimestampMixin

class Volume(SlugMixin, TimestampMixin, models.Model):
    """
    Modelo que representa um volume de um mangá.
    Um volume pode conter vários capítulos.
    """
    manga = models.ForeignKey(
        'Manga', 
        on_delete=models.CASCADE, 
        related_name='volumes',
        verbose_name=_('Mangá'),
        help_text=_('Mangá ao qual este volume pertence')
    )
    number = models.PositiveIntegerField(
        _('Número do Volume'),
        help_text=_('Número sequencial do volume')
    )
    title = models.CharField(
        _('Título'), 
        max_length=200, 
        blank=True,
        help_text=_('Título opcional do volume')
    )
    slug = models.SlugField(_('Slug'), unique=True, blank=True, max_length=255)
    cover_image = models.ImageField(
        _('Capa'), 
        upload_to='mangas/volumes/covers/%Y/%m/%d/', 
        null=True, 
        blank=True,
        help_text=_('Capa do volume')
    )
    is_published = models.BooleanField(
        _('Publicado?'), 
        default=True,
        help_text=_('Se o volume está visível publicamente')
    )
    
    class Meta:
        app_label = 'mangas'
        verbose_name = _('Volume')
        verbose_name_plural = _('Volumes')
        ordering = ['manga', 'number']
        unique_together = ['manga', 'number']
        indexes = [
            models.Index(fields=['manga', 'number']),
            models.Index(fields=['is_published']),
        ]
    
    def __str__(self):
        manga_title = self.manga.title if hasattr(self.manga, 'title') else 'Mangá Desconhecido'
        volume_str = f"{manga_title} - Volume {self.number}"
        return f"{volume_str}: {self.title}" if self.title else volume_str
    
    def save(self, *args, **kwargs):
        """Gera o slug automaticamente se não existir."""
        if not self.slug or self._state.adding:
            base_slug = f"volume-{self.number}"
            if self.manga and hasattr(self.manga, 'slug'):
                base_slug = f"{self.manga.slug}-{base_slug}"
            self.slug = self.generate_unique_slug(base_slug)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Retorna a URL para a visualização do volume."""
        from django.urls import reverse
        return reverse('mangas:volume_detail', kwargs={
            'manga_slug': self.manga.slug,
            'volume_slug': self.slug
        })
    
    def get_previous_volume(self):
        """Retorna o volume anterior, se existir."""
        return Volume.objects.filter(
            manga=self.manga,
            number__lt=self.number
        ).order_by('-number').first()
    
    def get_next_volume(self):
        """Retorna o próximo volume, se existir."""
        return Volume.objects.filter(
            manga=self.manga,
            number__gt=self.number
        ).order_by('number').first()
