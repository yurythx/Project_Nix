from django.urls import path
from apps.articles.views import (
    ArticleListView,
    ArticleDetailView,
    ArticleSearchView,
    ArticleCreateView,
    ArticleUpdateView,
    ArticleDeleteView,
    CategoryDetailView,
    CategoryListView,
    # TagDetailView,
    # TagListView,
)
# Views de comentários migradas para apps.comments.views


app_name = 'articles'

urlpatterns = [
    # Artigos - Listagem e busca
    path('', ArticleListView.as_view(), name='article_list'),
    path('busca/', ArticleSearchView.as_view(), name='search'),

    # Artigos - CRUD (Admin apenas)
    path('criar/', ArticleCreateView.as_view(), name='article_create'),
    path('<slug:slug>/editar/', ArticleUpdateView.as_view(), name='article_update'),
    path('<slug:slug>/deletar/', ArticleDeleteView.as_view(), name='article_delete'),

    # URLs de comentários disponíveis em apps.comments.urls

    # Categorias (deve vir antes dos slugs de artigo)
    path('categoria/', CategoryListView.as_view(), name='category_list'),
    path('categoria/<slug:slug>/', CategoryDetailView.as_view(), name='category_detail'),

    # Artigos - Detalhes (deve vir por último para não conflitar)
    path('<slug:slug>/', ArticleDetailView.as_view(), name='article_detail'),

    # Tags (implementar depois)
    # path('tag/', TagListView.as_view(), name='tag_list'),
    # path('tag/<slug:slug>/', TagDetailView.as_view(), name='tag_detail'),
]
