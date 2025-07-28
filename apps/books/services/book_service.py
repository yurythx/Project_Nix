from typing import List, Dict, Any, Optional
from django.db.models import QuerySet
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from apps.books.interfaces.services import IBookService
from apps.books.repositories.book_repository import BookRepository
from apps.books.models.book import Book, BookProgress, BookFavorite

User = get_user_model()

class BookService(IBookService):
    """
    Service para operações de livros
    
    Princípios SOLID aplicados:
    - Single Responsibility: Apenas operações de livros
    - Dependency Inversion: Depende da interface IBookService
    - Open/Closed: Extensível via herança
    """
    
    def __init__(self, repository: BookRepository = None):
        """
        Inicializa o service com injeção de dependência
        
        :param repository: Repository para acesso a dados
        """
        self.repository = repository or BookRepository()
    
    def get_all_books(self, limit: Optional[int] = None) -> QuerySet:
        """Obtém todos os livros"""
        books = self.repository.get_all()
        if limit:
            books = books[:limit]
        return books
    
    def get_book_by_slug(self, slug: str):
        """Obtém livro por slug"""
        try:
            return self.repository.get_by_slug(slug)
        except ObjectDoesNotExist:
            return None
    
    def search_books(self, query: str) -> QuerySet:
        """Busca livros por título"""
        return self.repository.search_by_title(query)
    
    def create_book(self, book_data: Dict[str, Any], created_by: User):
        """Cria um novo livro"""
        # Validações de negócio
        if not book_data.get('title'):
            raise ValueError("Título é obrigatório")
        
        # Adiciona usuário criador
        book_data['created_by'] = created_by
        
        return self.repository.create(book_data)
    
    def update_book(self, book_id: int, book_data: Dict[str, Any], updated_by: User):
        """Atualiza um livro"""
        # Validações de negócio
        if not book_data.get('title'):
            raise ValueError("Título é obrigatório")
        
        # Adiciona usuário que atualizou
        book_data['updated_by'] = updated_by
        
        return self.repository.update(book_id, book_data)
    
    def delete_book(self, book_id: int, deleted_by: User) -> bool:
        """Deleta um livro"""
        try:
            return self.repository.delete(book_id)
        except ObjectDoesNotExist:
            return False
    
    def get_book_progress(self, book_id: int, user: User):
        """Obtém progresso de leitura do usuário"""
        try:
            return BookProgress.objects.get(book_id=book_id, user=user)
        except BookProgress.DoesNotExist:
            return None
    
    def save_book_progress(self, book_id: int, user: User, progress_data: Dict[str, Any]):
        """Salva progresso de leitura"""
        progress, created = BookProgress.objects.get_or_create(
            book_id=book_id,
            user=user,
            defaults=progress_data
        )
        
        if not created:
            for key, value in progress_data.items():
                setattr(progress, key, value)
            progress.save()
        
        return progress
    
    def toggle_favorite(self, book_id: int, user: User) -> bool:
        """Alterna status de favorito"""
        try:
            favorite = BookFavorite.objects.get(book_id=book_id, user=user)
            favorite.delete()
            return False  # Desfavoritado
        except BookFavorite.DoesNotExist:
            BookFavorite.objects.create(book_id=book_id, user=user)
            return True  # Favoritado 