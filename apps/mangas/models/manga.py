from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.urls import reverse
from .base import SlugMixin, TimestampMixin

class Manga(SlugMixin, TimestampMixin, models.Model):
    """
    Modelo que representa um mangá.
    """
    title = models.CharField(_('Título'), max_length=200, help_text=_('Título do mangá'))
    author = models.CharField(_('Autor'), max_length=120, blank=True, help_text=_('Autor do mangá'))
    description = models.TextField(_('Descrição'), blank=True, help_text=_('Sinopse ou descrição do mangá'))
    cover_image = models.ImageField(
        _('Capa'), 
        upload_to='mangas/covers/%Y/%m/%d/', 
        null=True, 
        blank=True,
        help_text=_('Capa do mangá')
    )
    slug = models.SlugField(_('Slug'), unique=True, blank=True, max_length=255)
    is_published = models.BooleanField(_('Publicado?'), default=True, help_text=_('Se o mangá está visível publicamente'))

    class Meta:
        app_label = 'mangas'
        verbose_name = _('Mangá')
        verbose_name_plural = _('Mangás')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug'], name='manga_slug_idx'),
            models.Index(fields=['created_at'], name='manga_created_at_idx'),
            models.Index(fields=['is_published'], name='manga_published_idx'),
        ]

    def save(self, *args, **kwargs):
        """Sobrescreves o método save para garantir um slug único."""
        if not self.slug or self._state.adding:
            self.slug = self.generate_unique_slug(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """Retorna a URL absoluta para a visualização detalhada do mangá."""
        from django.urls import reverse
        return reverse('mangas:manga_detail', kwargs={'slug': self.slug})
    
    @property
    def status_display(self):
        """Retorna o status de publicação formatado."""
        return _('Publicado') if self.is_published else _('Rascunho')
    
    def get_cover_image_url(self):
        """
        Retorna a URL da imagem de capa ou uma URL padrão se não houver imagem.
        """
        if self.cover_image and hasattr(self.cover_image, 'url'):
            return self.cover_image.url
        return '/static/images/default-cover.jpg'
    
    def get_absolute_url(self):
        """Retorna a URL absoluta para a visualização detalhada do mangá."""
        return reverse('mangas:manga_detail', kwargs={'slug': self.slug})
    
    @property
    def status_display(self):
        """Retorna o status de publicação formatado."""
        return _('Publicado') if self.is_published else _('Rascunho')
    
    def save(self, *args, **kwargs):
        """Sobrescreve o método save para garantir um slug único."""
        if not self.slug or self._state.adding:
            self.slug = self.generate_unique_slug(self.title)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
