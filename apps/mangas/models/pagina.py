from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from .base import TimestampMixin, SlugMixin
# Removida a importação direta de Capitulo para evitar importação circular

class Pagina(TimestampMixin, SlugMixin, models.Model):
    """
    Modelo que representa uma página de um capítulo de mangá.
    """
    capitulo = models.ForeignKey(
        'Capitulo',  # Usando string para referência lazy
        on_delete=models.CASCADE,
        related_name='paginas',
        verbose_name=_('Capítulo'),
        help_text=_('Capítulo ao qual esta página pertence')
    )
    number = models.PositiveIntegerField(
        _('Número da Página'),
        help_text=_('Número sequencial da página no capítulo')
    )
    image = models.ImageField(
        _('Imagem'),
        upload_to='mangas/pages/%Y/%m/%d/',
        help_text=_('Imagem da página')
    )
    width = models.PositiveIntegerField(
        _('Largura'),
        blank=True,
        null=True,
        help_text=_('Largura da imagem em pixels')
    )
    height = models.PositiveIntegerField(
        _('Altura'),
        blank=True,
        null=True,
        help_text=_('Altura da imagem em pixels')
    )
    file_size = models.PositiveIntegerField(
        _('Tamanho do arquivo'),
        blank=True,
        null=True,
        help_text=_('Tamanho do arquivo em bytes')
    )
    content_type = models.CharField(
        _('Tipo de conteúdo'),
        max_length=100,
        blank=True,
        help_text=_('Tipo MIME da imagem')
    )
    slug = models.SlugField(
        _('Slug'),
        max_length=255,
        blank=True,
        help_text=_('Slug para URL amigável'),
        db_index=True
    )

    class Meta:
        app_label = 'mangas'
        verbose_name = _('Página')
        verbose_name_plural = _('Páginas')
        ordering = ['number']
        unique_together = ('capitulo', 'number')
        indexes = [
            models.Index(fields=['number'], name='page_number_idx'),
            models.Index(fields=['capitulo'], name='page_chapter_idx'),
        ]

    def __str__(self):
        return f'{self.capitulo} - Página {self.number}'
    
    def save(self, *args, **kwargs):
        """
        Sobrescreve o método save para extrair metadados da imagem e gerar slug.
        """
        # Extrai metadados da imagem se necessário
        if self.image and (not self.width or not self.height or not self.file_size or not self.content_type):
            try:
                from PIL import Image as PILImage
                import os
                import mimetypes
                # Abre a imagem para extrair dimensões
                with PILImage.open(self.image) as img:
                    self.width, self.height = img.size
                # Obtém informações do arquivo
                self.file_size = self.image.size
                # Corrige: obtém content_type de forma robusta
                if hasattr(self.image.file, 'content_type'):
                    self.content_type = self.image.file.content_type
                else:
                    mime, _ = mimetypes.guess_type(self.image.name)
                    self.content_type = mime or ''
            except Exception as e:
                # Se houver erro ao processar a imagem, apenas registra e continua
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Erro ao processar metadados da imagem: {str(e)}')
        
        # Verifica se é uma nova instância ou se houve mudanças relevantes
        is_new = self._state.adding
        
        # Para instâncias existentes, verifica se houve mudanças no número ou no capítulo
        needs_new_slug = False
        if not is_new and hasattr(self, 'pk') and self.pk:
            try:
                old_instance = self.__class__.objects.get(pk=self.pk)
                if old_instance.number != self.number or old_instance.capitulo_id != self.capitulo_id:
                    needs_new_slug = True
            except self.__class__.DoesNotExist:
                pass
        
        # Gera um novo slug se necessário
        if not self.slug or not self.slug.strip() or is_new or needs_new_slug:
            # Tenta obter o slug do capítulo para criar um slug hierárquico
            try:
                capitulo_slug = self.capitulo.slug
                base_slug = f"{capitulo_slug}-pagina-{self.number}"
            except (AttributeError, Exception):
                # Fallback se não conseguir obter o slug do capítulo
                base_slug = f"pagina-{self.capitulo_id}-{self.number}"
            
            # Gera um slug único
            self.slug = self.generate_unique_slug(base_slug, max_length=255)
        
        super().save(*args, **kwargs)
    
    def get_image_url(self):
        """Retorna a URL da imagem."""
        if self.image and hasattr(self.image, 'url'):
            return self.image.url
        return ''
    
    def get_image_dimensions(self):
        """Retorna as dimensões da imagem como string (Largura x Altura)."""
        if self.width and self.height:
            return f'{self.width} × {self.height} px'
        return _('Dimensões não disponíveis')
    
    def get_file_size_display(self):
        """Retorna o tamanho do arquivo formatado (KB, MB, etc.)."""
        if not self.file_size:
            return _('Tamanho não disponível')
            
        size = self.file_size
        for unit in ['bytes', 'KB', 'MB', 'GB']:
            if size < 1024.0 or unit == 'GB':
                if unit == 'bytes':
                    return f'{size} {unit}'
                return f'{size:.1f} {unit}'
            size /= 1024.0
