from typing import Any, Dict
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views import View

from apps.books.models.book import Book, BookProgress, BookFavorite
from apps.books.forms.book_form import BookForm
from apps.books.services.book_service import BookService
from apps.books.services.category_service import CategoryService

# BookListView removida - usando a versão mais completa em book_list_view.py

class BookDetailView(DetailView):
    """
    View para detalhes de um livro
    
    Princípios SOLID aplicados:
    - Single Responsibility: Apenas exibição de detalhes do livro
    - Open/Closed: Extensível via herança
    - Dependency Inversion: Usa serviços injetados
    """
    model = Book
    template_name = 'books/book_detail.html'
    context_object_name = 'book'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.book_service = BookService()
        self.category_service = CategoryService()
    
    def get_object(self, queryset=None):
        """Obtém o objeto e incrementa visualizações"""
        book = super().get_object(queryset)
        
        # Incrementa visualizações
        self.book_service.increment_book_views(book)
        
        return book

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Adiciona contexto extra"""
        context = super().get_context_data(**kwargs)
        book = self.object
        
        # Informações do arquivo
        file_name = book.file.name.lower() if book.file else ''
        context['is_epub'] = file_name.endswith('.epub')
        context['is_pdf'] = file_name.endswith('.pdf')
        
        # Livros relacionados da mesma categoria
        if book.category:
            related_books = self.book_service.get_books_by_category(book.category).exclude(id=book.id)[:6]
            context['related_books'] = related_books
        
        # Informações adicionais
        context.update({
            'page_title': book.title,
            'page_description': book.description or f'Leia {book.title} de {book.author}',
            'categories': self.category_service.get_active_categories(),
        })
        
        return context

class BookCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Book
    form_class = BookForm
    template_name = 'books/book_form.html'
    success_url = reverse_lazy('books:book_list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

class BookUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Book
    form_class = BookForm
    template_name = 'books/book_form.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    success_url = reverse_lazy('books:book_list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

class BookDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Book
    template_name = 'books/book_confirm_delete.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    success_url = reverse_lazy('books:book_list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser 

class SaveBookProgressView(LoginRequiredMixin, View):
    @method_decorator(csrf_exempt)
    def post(self, request, slug):
        from django.http import HttpResponseBadRequest, JsonResponse
        book = Book.objects.get(slug=slug)
        location = request.POST.get('location')
        if not location:
            return HttpResponseBadRequest('Localização não informada')
        progress, _ = BookProgress.objects.update_or_create(
            user=request.user, book=book,
            defaults={'location': location}
        )
        return JsonResponse({'status': 'ok'})

class GetBookProgressView(LoginRequiredMixin, View):
    def get(self, request, slug):
        from django.http import HttpResponseBadRequest, JsonResponse
        book = Book.objects.get(slug=slug)
        try:
            progress = BookProgress.objects.get(user=request.user, book=book)
            return JsonResponse({'location': progress.location})
        except BookProgress.DoesNotExist:
            return JsonResponse({'location': None})

class FavoriteBookView(LoginRequiredMixin, View):
    def post(self, request, slug):
        from django.http import HttpResponseBadRequest, JsonResponse
        book = Book.objects.get(slug=slug)
        BookFavorite.objects.get_or_create(user=request.user, book=book)
        return JsonResponse({'status': 'favorited'})

class UnfavoriteBookView(LoginRequiredMixin, View):
    def post(self, request, slug):
        from django.http import HttpResponseBadRequest, JsonResponse
        book = Book.objects.get(slug=slug)
        BookFavorite.objects.filter(user=request.user, book=book).delete()
        return JsonResponse({'status': 'unfavorited'})

class IsFavoriteBookView(LoginRequiredMixin, View):
    def get(self, request, slug):
        from django.http import HttpResponseBadRequest, JsonResponse
        book = Book.objects.get(slug=slug)
        is_fav = BookFavorite.objects.filter(user=request.user, book=book).exists()
        return JsonResponse({'favorite': is_fav})