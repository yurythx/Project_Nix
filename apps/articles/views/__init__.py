"""
Views do app articles seguindo princípios SOLID
"""
from .article_views import (
    BaseArticleView,
    ArticleListView,
    ArticleDetailView,
    ArticleSearchView,
    ArticleCreateView,
    ArticleUpdateView,
    ArticleDeleteView,
    CategoryDetailView,
    CategoryListView,
    EditorOrAdminRequiredMixin,
)
# Views de comentários migradas para apps.comments.views

__all__ = [
    'BaseArticleView',
    'ArticleListView',
    'ArticleDetailView',
    'ArticleSearchView',
    'ArticleCreateView',
    'ArticleUpdateView',
    'ArticleDeleteView',
    'CategoryDetailView',
    'CategoryListView',
    'EditorOrAdminRequiredMixin',
]
# Classes de comentários removidas - migradas para sistema global
