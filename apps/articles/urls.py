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
    CommentCreateView,
    ReplyCreateView,
    CommentListView,
    CommentModerationView,
    CommentModerationActionView,
    CommentStatsView,
    LoadMoreCommentsView,
    LoadRepliesView,
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
    path('admin/comentarios/', CommentModerationView.as_view(), name='moderate_comments'),
    path('admin/comentarios/<int:comment_id>/moderar/', CommentModerationActionView.as_view(), name='moderate_comment_action'),
    path('admin/comentarios/stats/', CommentStatsView.as_view(), name='comment_stats'),

    # Comentários
    path('<slug:slug>/comentarios/', CommentListView.as_view(), name='comment_list'),
    path('<slug:slug>/comentar/', CommentCreateView.as_view(), name='add_comment'),
    path('<slug:slug>/comentarios/<int:comment_id>/responder/', ReplyCreateView.as_view(), name='add_reply'),
    path('comentarios/', LoadMoreCommentsView.as_view(), name='load_more_comments'),
    path('comentarios/<int:comment_id>/replies/', LoadRepliesView.as_view(), name='load_replies'),

    # Artigos - Detalhes (deve vir por último para não conflitar)
    path('<slug:slug>/', ArticleDetailView.as_view(), name='article_detail'),

    # Categorias (implementar depois)
    path('categoria/', CategoryListView.as_view(), name='category_list'),
    path('categoria/<slug:slug>/', CategoryDetailView.as_view(), name='category_detail'),

    # Tags (implementar depois)
    # path('tag/', TagListView.as_view(), name='tag_list'),
    # path('tag/<slug:slug>/', TagDetailView.as_view(), name='tag_detail'),
]
