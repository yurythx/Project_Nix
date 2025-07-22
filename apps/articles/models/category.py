from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import MinLengthValidator

class Category(models.Model):
    """Modelo para categorias de artigos"""
    
    name = models.CharField(
        'nome',
        max_length=100,
        unique=True,
        validators=[MinLengthValidator(2)],
        help_text='Nome da categoria'
    )
    slug = models.SlugField(
        'slug',
        max_length=100,
        unique=True,
        help_text='URL amigável da categoria'
    )
    description = models.TextField(
        'descrição',
        blank=True,
        help_text='Descrição da categoria'
    )
    color = models.CharField(
        'cor',
        max_length=7,
        default='#007bff',
        help_text='Cor da categoria em hexadecimal (ex: #007bff)'
    )
    icon = models.CharField(
        'ícone',
        max_length=50,
        blank=True,
        help_text='Classe do ícone (ex: fas fa-newspaper)'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='categoria pai',
        help_text='Categoria pai para criar hierarquia'
    )
    is_active = models.BooleanField(
        'ativo',
        default=True,
        help_text='Se a categoria está ativa'
    )
    order = models.PositiveIntegerField(
        'ordem',
        default=0,
        help_text='Ordem de exibição da categoria'
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
        verbose_name = 'categoria'
        verbose_name_plural = 'categorias'
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active', 'order']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Gera slug automaticamente se não fornecido"""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Retorna URL absoluta da categoria"""
        return reverse('articles:category_detail', kwargs={'slug': self.slug})

    def get_children(self):
        """Retorna categorias filhas"""
        return self.__class__.objects.filter(
            parent=self,
            is_active=True
        ).order_by('order', 'name')

    def get_article_count(self):
        """Retorna número de artigos publicados na categoria"""
        return self.articles.filter(status='published').count()

    def get_breadcrumbs(self):
        """Retorna breadcrumbs da categoria"""
        breadcrumbs = []
        category = self
        while category:
            breadcrumbs.insert(0, category)
            category = category.parent
        return breadcrumbs

    @property
    def has_children(self):
        """Verifica se tem categorias filhas"""
        return self.get_children().exists()

    @property
    def seo_title(self):
        """Retorna título para SEO"""
        return self.meta_title or self.name

    @property
    def seo_description(self):
        """Retorna descrição para SEO"""
        return self.meta_description or self.description
