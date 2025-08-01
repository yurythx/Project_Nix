from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.urls import reverse
from django.contrib.auth import get_user_model
from .base import SlugMixin, TimestampMixin
from django.core.exceptions import ValidationError

User = get_user_model()

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
    criado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Criado por'),
        help_text=_('Usuário que criou este mangá')
    )
    view_count = models.PositiveIntegerField(
        _('Visualizações'),
        default=0,
        help_text=_('Número de visualizações do mangá')
    )

    class Meta:
        app_label = 'mangas'
        verbose_name = _('Mangá')
        verbose_name_plural = _('Mangás')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug'], name='manga_slug_idx'),
            models.Index(fields=['created_at'], name='manga_created_at_idx'),
            models.Index(fields=['is_published'], name='manga_published_idx'),
            models.Index(fields=['criado_por'], name='manga_criado_por_idx'),
        ]
        
    def save(self, *args, **kwargs):
        """
        Sobrescreve o método save para garantir que o slug seja gerado automaticamente
        se não estiver definido ou se o título for alterado.
        """
        # Validação completa do modelo
        self.full_clean()
        
        # Se o slug não existe ou o título foi alterado
        if not self.slug or (self.pk and 'title' in self.get_dirty_fields()):
            # Gera o slug a partir do título
            self.slug = self.generate_unique_slug(self.title)
            
        super().save(*args, **kwargs)
        
    def get_dirty_fields(self):
        """
        Retorna um dicionário com os campos que foram alterados no modelo.
        Útil para verificar se o título foi alterado.
        """
        if not self.pk:
            return {}
            
        # Obtém o estado atual do banco de dados
        current_state = self.__class__.objects.get(pk=self.pk)
        
        # Compara os campos
        dirty_fields = {}
        for field in self._meta.fields:
            if getattr(self, field.name) != getattr(current_state, field.name):
                dirty_fields[field.name] = getattr(current_state, field.name)
                
        return dirty_fields

    def clean(self):
        if not self.title or not self.title.strip():
            raise ValidationError({'title': 'O título é obrigatório.'})

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """Retorna a URL absoluta para a visualização detalhada do mangá."""
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
    
    def get_edit_url(self):
        """Retorna URL de edição do mangá"""
        try:
            return reverse('mangas:manga_edit', kwargs={'slug': self.slug})
        except:
            return None
