# Pacote de views do app audiobooks
from .category_views import (
    CategoryListView, CategoryDetailView, CategoryCreateView,
    CategoryUpdateView, CategoryDeleteView
)

__all__ = [
    'CategoryListView', 'CategoryDetailView', 'CategoryCreateView',
    'CategoryUpdateView', 'CategoryDeleteView'
]