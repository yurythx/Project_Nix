import os
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils.html import strip_tags, escape
from django.utils.safestring import mark_safe
import re
import bleach
from html import unescape

from tinymce.widgets import TinyMCE
from core.security import InputSanitizer

# Configuração de tags e atributos permitidos para o bleach
ALLOWED_TAGS = list(bleach.sanitizer.ALLOWED_TAGS.union([
    # Adicione seus tags extras aqui, ex:
    'p', 'img', 'span'
]))

ALLOWED_ATTRIBUTES = {
    **bleach.sanitizer.ALLOWED_ATTRIBUTES,
    'a': ['href', 'title', 'target', 'rel', 'class'],
    'img': ['src', 'alt', 'title', 'width', 'height', 'class', 'style'],
    'div': ['class', 'style'],
    'span': ['class', 'style'],
    'iframe': ['src', 'width', 'height', 'frameborder', 'allowfullscreen', 'class', 'style'],
    'video': ['controls', 'width', 'height', 'class', 'style'],
    'audio': ['controls', 'class', 'style'],
    'source': ['src', 'type'],
}

ALLOWED_STYLES = [
    'color', 'background-color', 'font-weight', 'text-align', 'text-decoration',
    'font-style', 'border', 'border-radius', 'padding', 'margin'
]

def sanitize_html(html_content):
    """Função para sanitizar conteúdo HTML mantendo formatação segura"""
    if not html_content:
        return ''
    
    # Decodificar entidades HTML
    html_content = unescape(html_content)
    
    # Sanitizar HTML com bleach (sem o argumento 'styles')
    cleaned = bleach.clean(
        html_content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )
    
    # Adicionar atributos de segurança a links externos
    cleaned = bleach.linkify(cleaned, parse_email=False, callbacks=[
        lambda attrs, new: add_link_attributes(attrs)
    ])
    
    return mark_safe(cleaned)

def add_link_attributes(attrs, new=False):
    """Adiciona atributos de segurança a links externos"""
    href_key = (None, 'href')
    
    if href_key not in attrs:
        return attrs
    
    href = attrs[href_key]
    if not href.startswith(('http://', 'https://', 'mailto:', 'tel:', '/', '#')):
        return None  # Remove links com protocolos não permitidos
    
    # Adiciona atributos de segurança para links externos
    if href.startswith(('http://', 'https://')) and not href.startswith('/'):
        attrs[(None, 'target')] = '_blank'
        attrs[(None, 'rel')] = 'noopener noreferrer'
    
    return attrs

from apps.articles.models.article import Article
from apps.articles.models.category import Category
from apps.articles.models.tag import Tag
# Comentários agora usam o sistema global

User = get_user_model()


class ArticleForm(forms.ModelForm):
    """Formulário para criação e edição de artigos"""

    status = forms.ChoiceField(
        choices=[
            ('draft', 'Rascunho'),
            ('published', 'Publicado'),
            ('archived', 'Arquivado'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='draft',
        label='Status',
        help_text='Status de publicação do artigo'
    )
    
    class Meta:
        model = Article
        fields = [
            'title', 'excerpt', 'content', 'featured_image', 'featured_image_alt',
            'category', 'tags', 'status', 'is_featured', 'allow_comments',
            'meta_title', 'meta_description', 'meta_keywords'
        ]
        
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Digite o título do artigo...',
                'maxlength': 200
            }),
            'excerpt': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Escreva um resumo atrativo do artigo...',
                'rows': 3,
                'maxlength': 500
            }),
            'content': TinyMCE(attrs={
                'class': 'tinymce',
                'placeholder': 'Escreva o conteúdo completo do artigo...',
                'style': 'min-height:400px;'
            }),
            'featured_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'featured_image_alt': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Texto alternativo para a imagem...',
                'maxlength': 200
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tags': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '5'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'allow_comments': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'meta_title': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Título para SEO (máx. 60 caracteres)',
                'maxlength': 60
            }),
            'meta_description': forms.Textarea(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Descrição para SEO (máx. 160 caracteres)',
                'rows': 3,
                'maxlength': 160
            }),
            'meta_keywords': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Palavras-chave separadas por vírgula',
                'maxlength': 200
            }),
        }
        
        labels = {
            'title': 'Título',
            'excerpt': 'Resumo',
            'content': 'Conteúdo',
            'featured_image': 'Imagem Destacada',
            'featured_image_alt': 'Texto Alternativo',
            'category': 'Categoria',
            'tags': 'Tags',
            'status': 'Status',
            'is_featured': 'Artigo em destaque',
            'allow_comments': 'Permitir comentários',
            'meta_title': 'Meta Título',
            'meta_description': 'Meta Descrição',
            'meta_keywords': 'Palavras-chave',
        }
        
        help_texts = {
            'title': 'Título principal do artigo (máximo 200 caracteres)',
            'excerpt': 'Resumo que aparecerá na listagem de artigos (máximo 500 caracteres)',
            'content': 'Conteúdo completo do artigo (pode usar HTML)',
            'featured_image': 'Imagem que aparecerá no topo do artigo e na listagem',
            'featured_image_alt': 'Texto alternativo para acessibilidade',
            'category': 'Categoria principal do artigo',
            'tags': 'Segure Ctrl/Cmd para selecionar múltiplas tags',
            'status': 'Status de publicação do artigo',
            'is_featured': 'Marque para destacar o artigo na página inicial',
            'allow_comments': 'Permitir que usuários comentem no artigo',
            'meta_title': 'Título para mecanismos de busca (máximo 60 caracteres)',
            'meta_description': 'Descrição para mecanismos de busca (máximo 160 caracteres)',
            'meta_keywords': 'Palavras-chave para SEO, separadas por vírgula',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar queryset para categoria
        self.fields['category'].queryset = Category.objects.all()
        self.fields['category'].empty_label = "Selecione uma categoria"
        
        # Configurar queryset para tags
        self.fields['tags'].queryset = Tag.objects.all()
        
        # Tornar campos obrigatórios
        self.fields['title'].required = True
        self.fields['excerpt'].required = True
        self.fields['content'].required = True
        
        # Inicializar o status do artigo
        if self.instance.pk:
            self.fields['status'].initial = self.instance.status
        else:
            self.fields['status'].initial = 'draft'

    def clean_title(self):
        """Validação e sanitização do título"""
        title = self.cleaned_data.get('title')
        if title:
            # Remover tags HTML e espaços extras
            title = strip_tags(title).strip()
            
            # Verificar se já existe um artigo com o mesmo título (exceto o atual)
            existing = Article.objects.filter(title__iexact=title)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError('Já existe um artigo com este título.')
            
            # Validar comprimento mínimo e máximo
            if len(title) < 5:
                raise ValidationError('O título deve ter pelo menos 5 caracteres.')
            if len(title) > 200:
                raise ValidationError('O título não pode ter mais de 200 caracteres.')
        
        return title

    def clean_excerpt(self):
        """Validação e sanitização do resumo"""
        excerpt = self.cleaned_data.get('excerpt')
        if excerpt:
            # Sanitizar HTML e remover tags perigosas
            excerpt = sanitize_html(excerpt)
            
            # Remover tags HTML para validação de comprimento
            plain_text = strip_tags(excerpt).strip()
            
            if len(plain_text) < 50:
                raise ValidationError('O resumo deve ter pelo menos 50 caracteres.')
            if len(plain_text) > 500:
                raise ValidationError('O resumo não pode ter mais de 500 caracteres.')
        
        return excerpt

    def clean_content(self):
        """Validação e sanitização do conteúdo"""
        content = self.cleaned_data.get('content')
        if content:
            # Sanitizar HTML mantendo formatação segura
            content = sanitize_html(content)
            
            # Remover tags HTML para validação de comprimento
            plain_text = strip_tags(content).strip()
            
            if len(plain_text) < 100:
                raise ValidationError('O conteúdo deve ter pelo menos 100 caracteres.')
            
            # Verificar e limitar o tamanho do conteúdo HTML
            if len(content) > 200000:  # ~200KB
                raise ValidationError('O conteúdo é muito grande. Por favor, reduza o tamanho.')
        
        return content

    def clean_meta_title(self):
        """Validação e sanitização do meta título"""
        meta_title = self.cleaned_data.get('meta_title')
        if meta_title:
            # Remover tags HTML e espaços extras
            meta_title = strip_tags(meta_title).strip()
            
            if len(meta_title) > 60:
                raise ValidationError('O meta título não pode ter mais de 60 caracteres.')
        
        return meta_title

    def clean_meta_description(self):
        """Validação e sanitização da meta descrição"""
        meta_description = self.cleaned_data.get('meta_description')
        if meta_description:
            # Remover tags HTML e espaços extras
            meta_description = strip_tags(meta_description).strip()
            
            if len(meta_description) > 160:
                raise ValidationError('A meta descrição não pode ter mais de 160 caracteres.')
        
        return meta_description

    def clean_featured_image(self):
        """Validação para imagem destacada"""
        image = self.cleaned_data.get('featured_image')
        if image:
            # Verificar tipo de arquivo
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            ext = os.path.splitext(image.name)[1].lower()
            if ext not in valid_extensions:
                raise ValidationError('Formato de arquivo não suportado. Use JPG, PNG, GIF ou WebP.')
            
            # Verificar tamanho do arquivo (máximo 5MB)
            if image.size > 5 * 1024 * 1024:
                raise ValidationError('A imagem não pode ser maior que 5MB.')
            
            # Verificar tipo de arquivo
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            if hasattr(image, 'content_type') and image.content_type not in allowed_types:
                raise ValidationError('Tipo de arquivo não permitido. Use JPEG, PNG, GIF ou WebP.')
        
        return image

    def save(self, commit=True):
        """Sobrescrever save para adicionar lógica personalizada"""
        article = super().save(commit=False)
        from django.utils import timezone

        # Define published_at conforme o status
        if article.status == 'published' and not article.published_at:
            article.published_at = timezone.now()
        elif article.status != 'published':
            article.published_at = None

        # Se não há meta_title, usar o título
        if not article.meta_title:
            article.meta_title = article.title[:60]

        # Se não há meta_description, usar o excerpt
        if not article.meta_description:
            article.meta_description = article.excerpt[:160]

        if commit:
            article.save()
            self.save_m2m()  # Salvar tags
        return article


# Formulários de comentários migrados para apps.comments.forms
