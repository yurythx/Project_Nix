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
    extracted = models.BooleanField(
        _('Extraído?'),
        default=False,
        help_text=_('Indica se as páginas do volume foram extraídas com sucesso')
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
        """Gera o slug automaticamente se não existir ou se o número do volume ou mangá mudar."""
        # Verifica se é uma nova instância ou se houve mudanças relevantes
        is_new = self._state.adding
        
        # Para instâncias existentes, verifica se houve mudanças no número ou no mangá
        needs_new_slug = False
        if not is_new and hasattr(self, 'pk') and self.pk:
            try:
                old_instance = self.__class__.objects.get(pk=self.pk)
                if old_instance.number != self.number or old_instance.manga_id != self.manga_id:
                    needs_new_slug = True
            except self.__class__.DoesNotExist:
                pass
        
        # Gera um novo slug se necessário
        if not self.slug or not self.slug.strip() or is_new or needs_new_slug:
            # Cria um slug base com o número do volume
            base_slug = f"volume-{self.number}"
            
            # Adiciona o slug do mangá se disponível
            if self.manga and hasattr(self.manga, 'slug') and self.manga.slug:
                base_slug = f"{self.manga.slug}-{base_slug}"
            
            # Gera um slug único
            self.slug = self.generate_unique_slug(base_slug, max_length=255)
        
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
        
    def listar_capitulos(self):
        """Lista todos os capítulos do volume com informações detalhadas."""
        cap_list = []
        for cap in self.capitulos.all():
            cap_info = {
                'id': cap.id,
                'number': cap.number,
                'title': cap.title,
                'slug': cap.slug,
                'is_published': cap.is_published,
                'num_paginas': cap.paginas.count(),
                'created_at': cap.created_at,
                'updated_at': cap.updated_at
            }
            cap_list.append(cap_info)
        return cap_list
