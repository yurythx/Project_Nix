"""
Testes para o serviço de mangá.
"""
import pytest
from unittest.mock import Mock, patch
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.mangas.models.manga import Manga
from apps.mangas.models.capitulo import Capitulo
from apps.mangas.models.pagina import Pagina
from apps.mangas.services.manga_service import MangaService
from apps.mangas.exceptions import (
    MangaNotFoundError,
    ChapterNotFoundError,
    PageNotFoundError,
    DuplicateMangaError,
    DuplicateChapterError,
    DuplicatePageError,
    MangaValidationError,
    MangaException,
    InvalidFileError,
    FileTooLargeError,
    UnsupportedFileTypeError,
    MangaPublishingError,
    ChapterPublishingError,
    PageProcessingError
)

# Fixtures para os testes
@pytest.fixture
def manga_repository_mock():
    """Retorna um mock do repositório de mangá."""
    return Mock()

@pytest.fixture
def manga_service(manga_repository_mock):
    """Retorna uma instância do serviço de mangá com o repositório mockado."""
    return MangaService(manga_repository=manga_repository_mock)

# Testes para o serviço de mangá
class TestMangaService:
    """Testes para o serviço de mangá."""
    
    def test_get_manga_by_slug_success(self, manga_service, manga_repository_mock):
        """Testa a obtenção de um mangá por slug com sucesso."""
        # Configuração do mock
        manga_mock = Manga(title="One Piece", slug="one-piece")
        manga_repository_mock.get_manga_by_slug.return_value = manga_mock
        
        # Execução
        resultado = manga_service.get_manga_by_slug("one-piece")
        
        # Verificações
        assert resultado == manga_mock
        manga_repository_mock.get_manga_by_slug.assert_called_once_with("one-piece")
    
    def test_get_manga_by_slug_not_found(self, manga_service, manga_repository_mock):
        """Testa a tentativa de obter um mangá inexistente por slug."""
        # Configuração do mock para levantar exceção
        manga_repository_mock.get_manga_by_slug.return_value = None
        
        # Verificação da exceção
        with pytest.raises(MangaNotFoundError):
            manga_service.get_manga_by_slug("inexistente")
    
    def test_create_manga_success(self, manga_service, manga_repository_mock):
        """Testa a criação de um novo mangá com sucesso."""
        # Dados de entrada
        user_mock = Mock()
        manga_data = {
            "title": "Naruto",
            "description": "História de um ninja",
            "author": "Masashi Kishimoto",
            "is_published": True,
            "cover_image": None
        }
        
        # Configuração do mock
        manga_created = Manga(slug="naruto", **manga_data)
        manga_repository_mock.create_manga.return_value = manga_created
        
        # Execução
        resultado = manga_service.create_manga(manga_data, user_mock)
        
        # Verificações
        assert resultado == manga_created
        manga_repository_mock.create_manga.assert_called_once()
        assert manga_repository_mock.create_manga.call_args[0][0]["created_by"] == user_mock
    
    def test_create_manga_duplicate_title(self, manga_service, manga_repository_mock):
        """Testa a tentativa de criar um mangá com título duplicado."""
        # Configuração do mock para simular violação de unicidade
        manga_repository_mock.create_manga.side_effect = DuplicateMangaError("Já existe um mangá com este título.")
        
        # Dados de entrada
        user_mock = Mock()
        manga_data = {"title": "Dragon Ball"}  # Título que já existe
        
        # Verificação da exceção
        with pytest.raises(DuplicateMangaError):
            manga_service.create_manga(manga_data, user_mock)
    
    def test_update_manga_success(self, manga_service, manga_repository_mock):
        """Testa a atualização de um mangá com sucesso."""
        # Dados de entrada
        slug = "one-piece"
        update_data = {"title": "One Piece - Novo"}
        user_mock = Mock()
        
        # Configuração do mock
        existing_manga = Manga(id=1, title="One Piece", slug=slug, author="Eiichiro Oda")
        updated_manga = Manga(id=1, title="One Piece - Novo", slug="one-piece-novo", author="Eiichiro Oda")
        
        manga_repository_mock.get_manga_by_slug.return_value = existing_manga
        manga_repository_mock.update_manga.return_value = updated_manga
        
        # Execução
        result = manga_service.update_manga(slug, update_data, user_mock)
        
        # Verificações
        assert result == updated_manga
        manga_repository_mock.get_manga_by_slug.assert_called_once_with(slug)
        manga_repository_mock.update_manga.assert_called_once()
    
    def test_delete_manga_success(self, manga_service, manga_repository_mock):
        """Testa a exclusão de um mangá com sucesso."""
        # Configuração do mock
        slug = "one-piece"
        user_mock = Mock()
        manga_mock = Mock()
        manga_repository_mock.get_manga_by_slug.return_value = manga_mock
        
        # Execução
        manga_service.delete_manga(slug, user_mock)
        
        # Verificações
        manga_repository_mock.get_manga_by_slug.assert_called_once_with(slug)
        manga_mock.delete.assert_called_once()
    
    def test_add_chapter_success(self, manga_service, manga_repository_mock):
        """Testa a adição de um capítulo a um mangá com sucesso."""
        # Dados de entrada
        manga_slug = "one-piece"
        user_mock = Mock()
        chapter_data = {
            "title": "Chapter 1",
            "number": 1,
            "volume": 1,
            "is_published": False
        }
        
        # Configuração do mock
        manga_mock = Mock()
        manga_repository_mock.get_manga_by_slug.return_value = manga_mock
        
        created_chapter = Capitulo(
            manga=manga_mock,
            slug="one-piece-chapter-1",
            **chapter_data
        )
        
        manga_repository_mock.create_chapter.return_value = created_chapter
        
        # Execução
        result = manga_service.create_chapter(manga_slug, chapter_data, user_mock)
        
        # Verificações
        assert result == created_chapter
        manga_repository_mock.get_manga_by_slug.assert_called_once_with(manga_slug)
        manga_repository_mock.create_chapter.assert_called_once()
        assert manga_repository_mock.create_chapter.call_args[0][0]["created_by"] == user_mock

# Mais testes podem ser adicionados para cobrir outros cenários e casos de borda
