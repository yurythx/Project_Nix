from typing import Any, Dict
from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404
from django.http import Http404

from apps.books.models.category import Category
from apps.books.services.category_service import CategoryService
from apps.books.services.book_service import BookService

class CategoryListView(ListView):
    """
    View para listagem de categorias
    
    Princípios SOLID aplicados:
    - Single Responsibility: Apenas listagem de categorias
    - Open/Closed: Extensível via herança
    - Dependency Inversion: Usa serviços injetados
    """
    model = Category
    template_name = 'books/category_list.html'
    context_object_name = 'categories'
    paginate_by = 12
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.category_service = CategoryService()
    
    def get_queryset(self):
        """Retorna apenas categorias ativas com livros"""
        return self.category_service.get_categories_with_books()
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Adiciona contexto extra"""
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Categorias de Livros',
            'page_description': 'Explore nossa coleção de livros organizados por categoria',
        })
        return context

class BookCategoryView(ListView):
    """
    View para exibir livros de uma categoria específica
    
    Princípios SOLID aplicados:
    - Single Responsibility: Apenas exibição de livros por categoria
    - Open/Closed: Extensível via herança
    - Dependency Inversion: Usa serviços injetados
    """
    template_name = 'books/book_category.html'
    context_object_name = 'books'
    paginate_by = 12
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.category_service = CategoryService()
        self.book_service = BookService()
        self.category = None
    
    def get_queryset(self):
        """Retorna livros da categoria especificada"""
        category_slug = self.kwargs.get('category_slug')
        
        # Obtém a categoria pelo slug
        self.category = self.category_service.get_category_by_slug(category_slug)
        
        if not self.category:
            raise Http404("Categoria não encontrada")
        
        # Retorna livros da categoria
        return self.book_service.get_books_by_category(self.category)
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Adiciona contexto extra"""
        context = super().get_context_data(**kwargs)
        
        # Adiciona informações da categoria
        context.update({
            'category': self.category,
            'page_title': f'Livros - {self.category.name}',
            'page_description': self.category.description or f'Livros da categoria {self.category.name}',
            'categories': self.category_service.get_active_categories(),
        })
        
        return context