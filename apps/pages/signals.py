from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from apps.pages.models import Page, NavigationItem, SEOSettings
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Page)
def page_saved(sender, instance, created, **kwargs):
    """Signal executado quando uma página é salva"""
    # Limpa cache relacionado a páginas
    cache.delete('homepage')
    cache.delete('menu_pages')
    cache.delete('published_pages')
    
    # Log da ação
    action = 'criada' if created else 'atualizada'
    logger.info(f"Página {action}: {instance.title}")

@receiver(post_delete, sender=Page)
def page_deleted(sender, instance, **kwargs):
    """Signal executado quando uma página é deletada"""
    # Limpa cache relacionado a páginas
    cache.delete('homepage')
    cache.delete('menu_pages')
    cache.delete('published_pages')
    
    # Log da ação
    logger.info(f"Página deletada: {instance.title}")

@receiver(post_save, sender=NavigationItem)
def navigation_saved(sender, instance, created, **kwargs):
    """Signal executado quando um item de navegação é salvo"""
    # Limpa cache de navegação
    cache.delete('main_navigation')
    
    # Log da ação
    action = 'criado' if created else 'atualizado'
    logger.info(f"Item de navegação {action}: {instance.title}")

@receiver(post_delete, sender=NavigationItem)
def navigation_deleted(sender, instance, **kwargs):
    """Signal executado quando um item de navegação é deletado"""
    # Limpa cache de navegação
    cache.delete('main_navigation')
    
    # Log da ação
    logger.info(f"Item de navegação deletado: {instance.title}")

@receiver(post_save, sender=SEOSettings)
def seo_settings_saved(sender, instance, created, **kwargs):
    """Signal executado quando configurações de SEO são salvas"""
    # Limpa cache de SEO
    cache.delete('seo_settings')
    
    # Log da ação
    action = 'criadas' if created else 'atualizadas'
    logger.info(f"Configurações de SEO {action}")

# Signal para limpar cache quando necessário
def clear_pages_cache():
    """Limpa todo o cache relacionado a páginas"""
    cache_keys = [
        'homepage',
        'menu_pages', 
        'published_pages',
        'main_navigation',
        'seo_settings',
        'popular_pages',
    ]
    
    for key in cache_keys:
        cache.delete(key)
    
    logger.info("Cache de páginas limpo")
