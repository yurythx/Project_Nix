from django.urls import path
from apps.books.views.book_views import (
    BookListView, BookDetailView, BookCreateView, BookUpdateView, BookDeleteView,
    SaveBookProgressView, GetBookProgressView,
    FavoriteBookView, UnfavoriteBookView, IsFavoriteBookView
)

app_name = 'books'

urlpatterns = [
    path('', BookListView.as_view(), name='book_list'),
    path('novo/', BookCreateView.as_view(), name='book_create'),
    path('<slug:slug>/', BookDetailView.as_view(), name='book_detail'),
    path('<slug:slug>/editar/', BookUpdateView.as_view(), name='book_edit'),
    path('<slug:slug>/deletar/', BookDeleteView.as_view(), name='book_delete'),
    # API progresso de leitura
    path('<slug:slug>/progress/save/', SaveBookProgressView.as_view(), name='book_progress_save'),
    path('<slug:slug>/progress/', GetBookProgressView.as_view(), name='book_progress_get'),
    # API favoritos
    path('<slug:slug>/favorite/', FavoriteBookView.as_view(), name='book_favorite'),
    path('<slug:slug>/unfavorite/', UnfavoriteBookView.as_view(), name='book_unfavorite'),
    path('<slug:slug>/favorite/status/', IsFavoriteBookView.as_view(), name='book_favorite_status'),
] 