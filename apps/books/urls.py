from django.urls import path
from apps.books.views.book_views import (
    BookListView, BookDetailView, BookCreateView, BookUpdateView, BookDeleteView,
    save_book_progress, get_book_progress,
    favorite_book, unfavorite_book, is_favorite_book
)

app_name = 'books'

urlpatterns = [
    path('', BookListView.as_view(), name='book_list'),
    path('novo/', BookCreateView.as_view(), name='book_create'),
    path('<slug:slug>/', BookDetailView.as_view(), name='book_detail'),
    path('<slug:slug>/editar/', BookUpdateView.as_view(), name='book_edit'),
    path('<slug:slug>/deletar/', BookDeleteView.as_view(), name='book_delete'),
    # API progresso de leitura
    path('<slug:slug>/progress/save/', save_book_progress, name='book_progress_save'),
    path('<slug:slug>/progress/', get_book_progress, name='book_progress_get'),
    # API favoritos
    path('<slug:slug>/favorite/', favorite_book, name='book_favorite'),
    path('<slug:slug>/unfavorite/', unfavorite_book, name='book_unfavorite'),
    path('<slug:slug>/favorite/status/', is_favorite_book, name='book_favorite_status'),
] 