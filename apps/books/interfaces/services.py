from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from django.db.models import QuerySet
from django.contrib.auth import get_user_model

User = get_user_model()

class IBookService(ABC):
    """Interface para serviços de livros"""
    
    @abstractmethod
    def get_all_books(self, limit: Optional[int] = None) -> QuerySet:
        """
        Obtém todos os livros
        :param limit: Limite de resultados
        :return: QuerySet de livros
        """
        pass
    
    @abstractmethod
    def get_book_by_slug(self, slug: str):
        """
        Obtém livro por slug
        :param slug: Slug do livro
        :return: Livro encontrado
        """
        pass
    
    @abstractmethod
    def search_books(self, query: str) -> QuerySet:
        """
        Busca livros por título
        :param query: Termo de busca
        :return: QuerySet de livros encontrados
        """
        pass
    
    @abstractmethod
    def create_book(self, book_data: Dict[str, Any], created_by: User):
        """
        Cria um novo livro
        :param book_data: Dados do livro
        :param created_by: Usuário que está criando
        :return: Livro criado
        """
        pass
    
    @abstractmethod
    def update_book(self, book_id: int, book_data: Dict[str, Any], updated_by: User):
        """
        Atualiza um livro
        :param book_id: ID do livro
        :param book_data: Dados para atualização
        :param updated_by: Usuário que está atualizando
        :return: Livro atualizado
        """
        pass
    
    @abstractmethod
    def delete_book(self, book_id: int, deleted_by: User) -> bool:
        """
        Deleta um livro
        :param book_id: ID do livro
        :param deleted_by: Usuário que está deletando
        :return: True se deletado com sucesso
        """
        pass
    
    @abstractmethod
    def get_book_progress(self, book_id: int, user: User):
        """
        Obtém progresso de leitura do usuário
        :param book_id: ID do livro
        :param user: Usuário
        :return: Progresso de leitura
        """
        pass
    
    @abstractmethod
    def save_book_progress(self, book_id: int, user: User, progress_data: Dict[str, Any]):
        """
        Salva progresso de leitura
        :param book_id: ID do livro
        :param user: Usuário
        :param progress_data: Dados do progresso
        """
        pass
    
    @abstractmethod
    def toggle_favorite(self, book_id: int, user: User) -> bool:
        """
        Alterna status de favorito
        :param book_id: ID do livro
        :param user: Usuário
        :return: True se favoritado, False se desfavoritado
        """
        pass 