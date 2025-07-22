from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator
from django.utils import timezone

User = get_user_model()

class ArticleQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status='published', published_at__lte=models.functions.Now())

class Article(models.Model):
    """
    Modelo para artigos do blog.
    Inclui campos para SEO, status, imagem destacada, legenda, analytics, etc.
    """
    
    STATUS_CHOICES = [
        ('draft', 'Rascunho'),
        ('published', 'Publicado'),
        ('archived', 'Arquivado'),
        ('scheduled', 'Agendado'),
    ]
    
    title = models.CharField(
        'título',
        max_length=200,
        validators=[MinLengthValidator(5)],
        help_text='Título do artigo'
    )
    slug = models.SlugField(
        'slug',
        max_length=200,
        unique=True,
        help_text='URL amigável do artigo'
    )
    excerpt = models.TextField(
        'resumo',
        max_length=500,
        help_text='Resumo do artigo para listagens e SEO'
    )
    content = models.TextField(
        'conteúdo',
        help_text='Conteúdo completo do artigo'
    )
    featured_image = models.ImageField(
        'imagem destacada',
        upload_to='articles/images/',
        blank=True,
        help_text='Imagem principal do artigo'
    )
    image_caption = models.CharField(
        'legenda da imagem',
        max_length=255,
        blank=True,
        help_text='Legenda opcional para a imagem destacada'
    )
    featured_image_alt = models.CharField(
        'texto alternativo da imagem',
        max_length=200,
        blank=True,
        help_text='Texto alternativo para acessibilidade'
    )
    
    # Relacionamentos
    category = models.ForeignKey(
        'articles.Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='articles',
        verbose_name='categoria',
        help_text='Categoria principal do artigo'
    )
    tags = models.ManyToManyField(
        'articles.Tag',
        blank=True,
        related_name='articles',
        verbose_name='tags',
        help_text='Tags relacionadas ao artigo'
    )
    
    # Status e publicação
    status = models.CharField(
        'status',
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        help_text='Status de publicação do artigo'
    )
    is_featured = models.BooleanField(
        'artigo em destaque',
        default=False,
        help_text='Se o artigo deve aparecer em destaque'
    )
    allow_comments = models.BooleanField(
        'permitir comentários',
        default=True,
        help_text='Se o artigo permite comentários'
    )
    
    # Autoria
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='authored_articles',
        verbose_name='autor',
        help_text='Autor principal do artigo'
    )
    contributors = models.ManyToManyField(
        User,
        blank=True,
        related_name='contributed_articles',
        verbose_name='colaboradores',
        help_text='Outros colaboradores do artigo'
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
    
    # Datas
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
    scheduled_at = models.DateTimeField(
        'agendado para',
        null=True,
        blank=True,
        help_text='Data e hora para publicação automática'
    )
    
    # Analytics
    view_count = models.PositiveIntegerField(
        'visualizações',
        default=0,
        help_text='Número de visualizações do artigo'
    )
    reading_time = models.PositiveIntegerField(
        'tempo de leitura',
        default=0,
        help_text='Tempo estimado de leitura em minutos'
    )

    objects = ArticleQuerySet.as_manager()

    class Meta:
        verbose_name = 'artigo'
        verbose_name_plural = 'artigos'
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['status', 'published_at']),
            models.Index(fields=['author', '-published_at']),
            models.Index(fields=['category', '-published_at']),
            models.Index(fields=['is_featured', '-published_at']),
        ]

    def __str__(self):
        return self.title

    def _generate_unique_slug(self):
        """Gera um slug único baseado no título"""
        if not self.title:
            return 'artigo-sem-titulo'

        base_slug = slugify(self.title)
        if not base_slug:
            base_slug = 'artigo-sem-titulo'

        slug = base_slug
        counter = 1

        # Verifica se o slug já existe (excluindo o próprio objeto se estiver editando)
        while Article.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        return slug

    def save(self, *args, **kwargs):
        """Gera slug automaticamente e calcula tempo de leitura"""
        # Gerar slug se não existe
        if not self.slug:
            self.slug = self._generate_unique_slug()
        else:
            # Verificação adicional de segurança para slug único
            if Article.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = self._generate_unique_slug()

        # Calcula tempo de leitura (aproximadamente 200 palavras por minuto)
        if self.content:
            word_count = len(self.content.split())
            self.reading_time = max(1, word_count // 200)

        # Define data de publicação se status mudou para published
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Retorna URL absoluta do artigo"""
        return reverse('articles:article_detail', kwargs={'slug': self.slug})

    def get_related_articles(self, limit=3):
        """Retorna artigos relacionados baseados na categoria e tags"""
        related = Article.objects.filter(
            status='published'
        ).exclude(id=self.id)
        
        # Prioriza artigos da mesma categoria
        if self.category:
            related = related.filter(category=self.category)
        
        # Se não há artigos da mesma categoria, busca por tags
        if not related.exists() and self.tags.exists():
            related = Article.objects.filter(
                tags__in=self.tags.all(),
                status='published'
            ).exclude(id=self.id).distinct()
        
        return related[:limit]

    def increment_view_count(self):
        """Incrementa contador de visualizações"""
        self.view_count += 1
        self.save(update_fields=['view_count'])

    @property
    def is_published(self):
        """Verifica se o artigo está publicado"""
        return self.status == 'published' and self.published_at

    @property
    def seo_title(self):
        """Retorna título para SEO"""
        return self.meta_title or self.title

    @property
    def seo_description(self):
        """Retorna descrição para SEO"""
        return self.meta_description or self.excerpt

    @property
    def comment_count(self):
        """Retorna número de comentários aprovados"""
        return self.comments.filter(is_approved=True).count()

    def can_be_commented(self):
        """Verifica se o artigo pode receber comentários"""
        return self.allow_comments and self.is_published
