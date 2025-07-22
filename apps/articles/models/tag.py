from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import MinLengthValidator

class Tag(models.Model):
    """Modelo para tags de artigos"""
    
    name = models.CharField(
        'nome',
        max_length=50,
        unique=True,
        validators=[MinLengthValidator(2)],
        help_text='Nome da tag'
    )
    slug = models.SlugField(
        'slug',
        max_length=50,
        unique=True,
        help_text='URL amigável da tag'
    )
    description = models.TextField(
        'descrição',
        blank=True,
        help_text='Descrição da tag'
    )
    color = models.CharField(
        'cor',
        max_length=7,
        default='#6c757d',
        help_text='Cor da tag em hexadecimal (ex: #6c757d)'
    )
    is_featured = models.BooleanField(
        'destaque',
        default=False,
        help_text='Se a tag deve aparecer em destaque'
    )
    
    # SEO Fields
    meta_title = models.CharField(
        'meta título',
        max_length=60,
        blank=True,
        help_text='Título para SEO (máximo 60 caracteres)'
    )
    meta_description = models.CharField(
        'meta descrição',
        max_length=160,
        blank=True,
        help_text='Descrição para SEO (máximo 160 caracteres)'
    )
    
    created_at = models.DateTimeField(
        'criado em',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        'atualizado em',
        auto_now=True
    )

    class Meta:
        verbose_name = 'tag'
        verbose_name_plural = 'tags'
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_featured']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Gera slug automaticamente se não fornecido"""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Retorna URL absoluta da tag"""
        return reverse('articles:tag_detail', kwargs={'slug': self.slug})

    def get_article_count(self):
        """Retorna número de artigos publicados com esta tag"""
        return self.articles.filter(status='published').count()

    @property
    def seo_title(self):
        """Retorna título para SEO"""
        return self.meta_title or f"Artigos sobre {self.name}"

    @property
    def seo_description(self):
        """Retorna descrição para SEO"""
        return self.meta_description or self.description or f"Todos os artigos relacionados à tag {self.name}"
