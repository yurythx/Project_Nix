from typing import Any, Dict
from django.views.generic import ListView
from django.db.models import QuerySet

from apps.books.services.book_service import BookService
from apps.books.services.category_service import CategoryService
from apps.books.models.book import Book

class BookListView(ListView):
    """
    View para listagem de livros
    
    Princípios SOLID aplicados:
    - Single Responsibility: Apenas listagem de livros
    - Open/Closed: Extensível via herança
    - Dependency Inversion: Usa serviços injetados
    """
    model = Book
    template_name = 'books/book_list.html'
    context_object_name = 'books'
    paginate_by = 12
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.book_service = BookService()
        self.category_service = CategoryService()
    
    def get_queryset(self) -> QuerySet:
        """Retorna livros com filtros aplicados"""
        # Obtém todos os livros públicos através do serviço
        queryset = self.book_service.get_all_books()
        
        # Filtro por categoria
        category = self.request.GET.get('category')
        if category:
            queryset = self.book_service.get_books_by_category(category)
            
        # Filtro por busca
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = self.book_service.search_books(search_query)
            
        # Ordenação
        sort_by = self.request.GET.get('sort_by', '-created_at')
        if sort_by in ['title', '-title', 'created_at', '-created_at', 'author', '-author']:
            queryset = queryset.order_by(sort_by)
            
        return queryset
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Adiciona contexto extra"""
        context = super().get_context_data(**kwargs)
        
        # Adiciona categorias para o filtro
        context.update({
            'categories': self.category_service.get_active_categories(),
            'current_category': self.request.GET.get('category', ''),
            'sort_by': self.request.GET.get('sort_by', '-created_at'),
            'search_query': self.request.GET.get('q', ''),
            'page_title': 'Biblioteca de Livros',
            'page_description': 'Explore nossa coleção completa de livros digitais',
        })
        
        # Adiciona livros em destaque se estiver na página principal (sem filtros)
        if not self.request.GET.get('q') and not self.request.GET.get('category'):
            context.update({
                'featured_books': self.book_service.get_featured_books(limit=5),
                'recent_books': self.book_service.get_all_books().order_by('-created_at')[:5],
            })
            
        return context