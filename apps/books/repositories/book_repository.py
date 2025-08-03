from typing import Optional, Union
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist

from apps.books.interfaces.book_repository import BookRepositoryInterface
from apps.books.models.book import Book
from apps.books.models.category import Category

class BookRepository(BookRepositoryInterface):
    """
    Repositório para operações de dados de livros
    
    Princípios SOLID aplicados:
    - Single Responsibility: Apenas acesso a dados de livros
    - Open/Closed: Extensível via herança
    - Liskov Substitution: Implementa completamente a interface
    """
    
    def get_all(self):
        """Lista todos os livros"""
        return Book.objects.all().select_related('category')
    
    def list_all(self):
        """Lista todos os livros (método de conveniência)"""
        return self.get_all()
    
    def get_by_id(self, book_id):
        """Obtém livro por ID"""
        try:
            return Book.objects.get(id=book_id)
        except ObjectDoesNotExist:
            return None
    
    def get_public_books(self) -> QuerySet:
        """Retorna apenas livros públicos"""
        return Book.objects.filter(is_public=True).select_related('category')
    
    def get_featured_books(self) -> QuerySet:
        """Retorna livros em destaque"""
        return Book.objects.filter(is_featured=True, is_public=True).select_related('category')

    def get_by_slug(self, slug):
        """Obtém livro por slug"""
        return get_object_or_404(Book, slug=slug)
    
    def get_by_category(self, category: Union[str, Category]) -> QuerySet:
        """Obtém livros por categoria"""
        if isinstance(category, Category):
            return Book.objects.filter(
                category=category, 
                is_public=True
            ).select_related('category')
        elif isinstance(category, str):
            return Book.objects.filter(
                category__slug=category, 
                is_public=True
            ).select_related('category')
        else:
            return Book.objects.none()
    
    def search_books(self, query: str) -> QuerySet:
        """Busca livros por título ou autor"""
        return Book.objects.filter(
            title__icontains=query,
            is_public=True
        ).select_related('category') | Book.objects.filter(
            author__icontains=query,
            is_public=True
        ).select_related('category')
    
    def increment_views(self, book: Book) -> None:
        """Incrementa o contador de visualizações"""
        book.views += 1
        book.save(update_fields=['views'])

    def create(self, data):
        """Cria um novo livro"""
        return Book.objects.create(**data)

    def update(self, slug, data):
        """Atualiza um livro existente"""
        book = self.get_by_slug(slug)
        for key, value in data.items():
            setattr(book, key, value)
        book.save()
        return book

    def delete(self, slug):
        """Exclui um livro"""
        book = self.get_by_slug(slug)
        book.delete()