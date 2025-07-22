from django import template
from django.utils import timezone
from apps.articles.models.article import Article

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
