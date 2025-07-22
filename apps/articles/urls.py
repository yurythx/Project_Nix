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
from apps.articles.views.comment_views import (
    add_comment,
    add_reply,
    comment_list,
    moderate_comments,
    moderate_comment_action,
    comment_stats,
    load_more_comments,
    load_replies,
)


app_name = 'articles'

urlpatterns = [
    # Artigos - Listagem e busca
    path('', ArticleListView.as_view(), name='article_list'),
    path('busca/', ArticleSearchView.as_view(), name='search'),

    # Artigos - CRUD (Admin apenas)
    path('criar/', ArticleCreateView.as_view(), name='article_create'),
    path('<slug:slug>/editar/', ArticleUpdateView.as_view(), name='article_update'),
    path('<slug:slug>/deletar/', ArticleDeleteView.as_view(), name='article_delete'),

    # Moderação de comentários (staff apenas) - deve vir antes dos slugs
    path('admin/comentarios/', moderate_comments, name='moderate_comments'),
    path('admin/comentarios/<int:comment_id>/moderar/', moderate_comment_action, name='moderate_comment_action'),
    path('admin/comentarios/stats/', comment_stats, name='comment_stats'),

    # Comentários
    path('<slug:slug>/comentarios/', comment_list, name='comment_list'),
    path('<slug:slug>/comentar/', add_comment, name='add_comment'),
    path('<slug:slug>/comentarios/<int:comment_id>/responder/', add_reply, name='add_reply'),
    path('comentarios/', load_more_comments, name='load_more_comments'),
    path('comentarios/<int:comment_id>/replies/', load_replies, name='load_replies'),

    # Artigos - Detalhes (deve vir por último para não conflitar)
    path('<slug:slug>/', ArticleDetailView.as_view(), name='article_detail'),

    # Categorias (implementar depois)
    path('categoria/', CategoryListView.as_view(), name='category_list'),
    path('categoria/<slug:slug>/', CategoryDetailView.as_view(), name='category_detail'),

    # Tags (implementar depois)
    # path('tag/', TagListView.as_view(), name='tag_list'),
    # path('tag/<slug:slug>/', TagDetailView.as_view(), name='tag_detail'),
]
