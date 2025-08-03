# Repositories para o app pages
from .page_repository import DjangoPageRepository
from .navigation_repository import DjangoNavigationRepository
from .seo_repository import DjangoSEORepository

__all__ = [
    'DjangoPageRepository',
    'DjangoNavigationRepository',
    'DjangoSEORepository',
]