from django import template
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.text import Truncator
from apps.articles.models.article import Article

import re

register = template.Library()


@register.simple_tag
def get_latest_articles(limit=5):
    """Retorna os últimos artigos publicados"""
    return Article.objects.filter(
        status='published',
        published_at__lte=timezone.now()
    ).select_related('author', 'category').prefetch_related('tags').order_by('-published_at')[:limit]


@register.simple_tag
def get_featured_articles(limit=3):
    """Retorna artigos em destaque"""
    return Article.objects.filter(
        status='published',
        is_featured=True,
        published_at__lte=timezone.now()
    ).select_related('author', 'category').order_by('-published_at')[:limit]


@register.simple_tag
def get_articles_by_category(category_slug, limit=5):
    """Retorna artigos de uma categoria específica"""
    return Article.objects.filter(
        category__slug=category_slug,
        status='published',
        published_at__lte=timezone.now()
    ).select_related('author', 'category').prefetch_related('tags').order_by('-published_at')[:limit]


@register.simple_tag
def get_popular_articles(limit=5):
    """Retorna artigos mais populares (por visualizações)"""
    return Article.objects.filter(
        status='published',
        published_at__lte=timezone.now()
    ).select_related('author', 'category').order_by('-view_count')[:limit]


@register.inclusion_tag('articles/includes/article_card.html')
def article_card(article, show_excerpt=True, show_author=True, show_date=True):
    """Renderiza um card de artigo"""
    return {
        'article': article,
        'show_excerpt': show_excerpt,
        'show_author': show_author,
        'show_date': show_date,
    }


@register.filter
def reading_time_text(minutes):
    """Converte tempo de leitura em texto amigável"""
    if minutes < 1:
        return "Menos de 1 min"
    elif minutes == 1:
        return "1 min"
    else:
        return f"{minutes} min"


@register.filter
def view_count_text(count):
    """Converte contador de visualizações em texto amigável"""
    if count < 1000:
        return str(count)
    elif count < 1000000:
        return f"{count/1000:.1f}k"
    else:
        return f"{count/1000000:.1f}M"


@register.filter(name='has_group')
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()


@register.filter
def clean_excerpt(text, length=120):
    """Remove HTML tags e limita o texto do excerpt"""
    if not text:
        return ""

    # Remove tags HTML
    clean_text = strip_tags(text)

    # Remove quebras de linha extras e espaços
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()

    # Trunca o texto
    truncator = Truncator(clean_text)
    return truncator.chars(length, truncate='...')


@register.filter
def clean_html(text):
    """Remove completamente as tags HTML do texto"""
    if not text:
        return ""

    # Remove tags HTML
    clean_text = strip_tags(text)

    # Remove quebras de linha extras e espaços
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()

    return clean_text


@register.filter
def clean_article_content(content):
    """Limpa o conteúdo do artigo removendo elementos problemáticos"""
    if not content:
        return ""

    # Remove elementos estruturais problemáticos
    content = re.sub(r'<article[^>]*class="[^"]*single-grid[^"]*"[^>]*>.*?</article>', '', content, flags=re.DOTALL)
    content = re.sub(r'<header[^>]*>.*?</header>', '', content, flags=re.DOTALL)
    content = re.sub(r'<footer[^>]*>.*?</footer>', '', content, flags=re.DOTALL)

    # Remove widgets e elementos comerciais
    content = re.sub(r'<div[^>]*class="[^"]*widget[^"]*"[^>]*>.*?</div>', '', content, flags=re.DOTALL)
    content = re.sub(r'<div[^>]*class="[^"]*achados[^"]*"[^>]*>.*?</div>', '', content, flags=re.DOTALL)
    content = re.sub(r'<div[^>]*class="[^"]*block-before-content[^"]*"[^>]*>.*?</div>', '', content, flags=re.DOTALL)
    content = re.sub(r'<div[^>]*class="[^"]*by[^"]*"[^>]*>.*?</div>', '', content, flags=re.DOTALL)
    content = re.sub(r'<div[^>]*class="[^"]*author[^"]*"[^>]*>.*?</div>', '', content, flags=re.DOTALL)
    content = re.sub(r'<div[^>]*class="[^"]*time[^"]*"[^>]*>.*?</div>', '', content, flags=re.DOTALL)
    content = re.sub(r'<div[^>]*class="[^"]*entry[^"]*"[^>]*>.*?</div>', '', content, flags=re.DOTALL)
    content = re.sub(r'<div[^>]*class="[^"]*grid8[^"]*"[^>]*>.*?</div>', '', content, flags=re.DOTALL)

    # Remove parágrafos problemáticos
    content = re.sub(r'<p[^>]*class="[^"]*flipboard-subtitle[^"]*"[^>]*>.*?</p>', '', content, flags=re.DOTALL)
    content = re.sub(r'<p[^>]*class="[^"]*olho[^"]*"[^>]*>.*?</p>', '', content, flags=re.DOTALL)

    # Remove atributos desnecessários mas mantém a estrutura
    content = re.sub(r'class="[^"]*"', '', content)
    content = re.sub(r'data-[^=]*="[^"]*"', '', content)
    content = re.sub(r'style="[^"]*"', '', content)
    content = re.sub(r'id="[^"]*"', '', content)

    # Limpa espaços extras
    content = re.sub(r'>\s+<', '><', content)
    content = re.sub(r'\s+', ' ', content)

    return content.strip()

