from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from .base import SlugMixin, TimestampMixin
from .volume import Volume  # Importa o modelo Volume

class Capitulo(SlugMixin, TimestampMixin, models.Model):
    """
    Modelo que representa um capítulo de um volume de mangá.
    """
    volume = models.ForeignKey(
        Volume, 
        on_delete=models.CASCADE, 
        related_name='capitulos',
        verbose_name=_('Volume'),
        help_text=_('Volume ao qual este capítulo pertence')
    )
    number = models.PositiveIntegerField(
        _('Número do Capítulo'),
        help_text=_('Número sequencial do capítulo')
    )
    title = models.CharField(
        _('Título'), 
        max_length=200, 
        blank=True,
        help_text=_('Título opcional do capítulo')
    )
    slug = models.SlugField(
        _('Slug'), 
        max_length=255, 
        blank=True,
        help_text=_('Identificador único para URLs')
    )
    is_published = models.BooleanField(
        _('Publicado?'), 
        default=True,
        help_text=_('Se o capítulo está visível publicamente')
    )
    views = models.PositiveIntegerField(
        _('Visualizações'),
        default=0,
        help_text=_('Número de visualizações do capítulo')
    )

    class Meta:
        app_label = 'mangas'
        verbose_name = _('Capítulo')
        verbose_name_plural = _('Capítulos')
        ordering = ['number']
        unique_together = ('volume', 'number')

    def __str__(self):
        if self.title:
            return f"{self.volume.manga.title} - {self.volume.number} - {self.number}: {self.title}"
        return f"{self.volume.manga.title} - {self.volume.number} - {self.number}"

    def save(self, *args, **kwargs):
        """
        Sobrescreve o método save para gerar o slug automaticamente.
        """
        if not self.slug:
            base_slug = f"{self.volume.manga.slug}-{self.volume.number}-{self.number}"
            if self.title:
                base_slug += f"-{slugify(self.title)}"
            self.slug = self.generate_unique_slug(base_slug)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """
        Retorna a URL para acessar este capítulo.
        """
        from django.urls import reverse
        return reverse('mangas:capitulo-detail', kwargs={
            'manga_slug': self.volume.manga.slug,
            'volume_number': self.volume.number,
            'chapter_number': self.number,
            'chapter_slug': self.slug
        })

    def get_next_chapter(self):
        """
        Retorna o próximo capítulo, se existir.
        """
        return Capitulo.objects.filter(
            volume__manga=self.volume.manga,
            volume__number__gte=self.volume.number,
            number__gt=self.number
        ).order_by('volume__number', 'number').first()

    def get_previous_chapter(self):
        """
        Retorna o capítulo anterior, se existir.
        """
        # Primeiro tenta encontrar no mesmo volume
        prev_in_volume = Capitulo.objects.filter(
            volume=self.volume,
            number__lt=self.number
        ).order_by('-number').first()
        
        if prev_in_volume:
            return prev_in_volume
            
        # Se não encontrar no mesmo volume, tenta no volume anterior
        prev_volume = self.volume.get_previous_volume()
        if prev_volume:
            return Capitulo.objects.filter(
                volume=prev_volume
            ).order_by('-number').first()
            
        return None

    @property
    def status_display(self):
        """Retorna o status de publicação formatado."""
        return _('Publicado') if self.is_published else _('Rascunho')
    @property
    def manga(self):
        """Propriedade para compatibilidade retroativa."""
        return self.volume.manga