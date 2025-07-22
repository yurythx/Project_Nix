from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator

User = get_user_model()

class Page(models.Model):
    """Modelo para páginas da aplicação"""
    
    STATUS_CHOICES = [
        ('draft', 'Rascunho'),
        ('published', 'Publicado'),
        ('archived', 'Arquivado'),
    ]
    
    TEMPLATE_CHOICES = [
        ('pages/default.html', 'Padrão'),
        ('pages/landing.html', 'Landing Page'),
        ('pages/full_width.html', 'Largura Total'),
        ('pages/sidebar.html', 'Com Sidebar'),
    ]
    
    title = models.CharField(
        'título',
        max_length=200,
        validators=[MinLengthValidator(3)],
        help_text='Título da página'
    )
    slug = models.SlugField(
        'slug',
        max_length=200,
        unique=True,
        help_text='URL amigável da página'
    )
    content = models.TextField(
        'conteúdo',
        help_text='Conteúdo da página em HTML ou Markdown'
    )
    excerpt = models.TextField(
        'resumo',
        max_length=500,
        blank=True,
        help_text='Resumo da página para SEO e listagens'
    )
    status = models.CharField(
        'status',
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        help_text='Status de publicação da página'
    )
    template = models.CharField(
        'template',
        max_length=100,
        choices=TEMPLATE_CHOICES,
        default='pages/default.html',
        help_text='Template a ser usado para renderizar a página'
    )
    is_homepage = models.BooleanField(
        'é página inicial',
        default=False,
        help_text='Define se esta é a página inicial do site'
    )
    show_in_menu = models.BooleanField(
        'mostrar no menu',
        default=True,
        help_text='Se a página deve aparecer no menu de navegação'
    )
    menu_order = models.PositiveIntegerField(
        'ordem no menu',
        default=0,
        help_text='Ordem de exibição no menu (menor número = primeiro)'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='página pai',
        help_text='Página pai para criar hierarquia'
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
    meta_keywords = models.CharField(
        'palavras-chave',
        max_length=255,
        blank=True,
        help_text='Palavras-chave separadas por vírgula'
    )
    
    # Tracking
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_pages',
        verbose_name='criado por'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_pages',
        verbose_name='atualizado por'
    )
    created_at = models.DateTimeField(
        'criado em',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        'atualizado em',
        auto_now=True
    )
    published_at = models.DateTimeField(
        'publicado em',
        null=True,
        blank=True,
        help_text='Data e hora de publicação'
    )
    
    # Analytics
    view_count = models.PositiveIntegerField(
        'visualizações',
        default=0,
        help_text='Número de visualizações da página'
    )

    class Meta:
        verbose_name = 'página'
        verbose_name_plural = 'páginas'
        ordering = ['menu_order', 'title']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['status', 'published_at']),
            models.Index(fields=['show_in_menu', 'menu_order']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """Gera slug automaticamente se não fornecido"""
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Garante que apenas uma página seja homepage
        if self.is_homepage:
            Page.objects.filter(is_homepage=True).exclude(pk=self.pk).update(is_homepage=False)
        
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Retorna URL absoluta da página"""
        if self.is_homepage:
            return reverse('pages:home')
        return reverse('pages:page_detail', kwargs={'slug': self.slug})

    def get_breadcrumbs(self):
        """Retorna breadcrumbs da página"""
        breadcrumbs = []
        page = self
        while page:
            breadcrumbs.insert(0, page)
            page = page.parent
        return breadcrumbs

    def get_children(self):
        """Retorna páginas filhas"""
        return self.page_set.filter(status='published').order_by('menu_order', 'title')

    def increment_view_count(self):
        """Incrementa contador de visualizações"""
        self.view_count += 1
        self.save(update_fields=['view_count'])

    @property
    def is_published(self):
        """Verifica se a página está publicada"""
        return self.status == 'published'

    @property
    def seo_title(self):
        """Retorna título para SEO"""
        return self.meta_title or self.title

    @property
    def seo_description(self):
        """Retorna descrição para SEO"""
        return self.meta_description or self.excerpt
