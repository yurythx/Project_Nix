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
from .comment_views import (
    CommentCreateView,
    ReplyCreateView,
    CommentListView,
    CommentModerationView,
    CommentModerationActionView,
    CommentStatsView,
    LoadMoreCommentsView,
    LoadRepliesView,
)

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
__all__ += [
    'CommentCreateView',
    'ReplyCreateView',
    'CommentListView',
    'CommentModerationView',
    'CommentModerationActionView',
    'CommentStatsView',
    'LoadMoreCommentsView',
    'LoadRepliesView',
]
