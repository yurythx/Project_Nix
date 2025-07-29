from django.db import models
from django.utils.translation import gettext_lazy as _
from .base import TimestampMixin
# Removida a importação direta de Capitulo para evitar importação circular

class Pagina(TimestampMixin, models.Model):
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
        Sobrescreve o método save para extrair metadados da imagem.
        """
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
