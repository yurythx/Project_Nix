from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, Tuple
from django.db.models import QuerySet, Model
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import UploadedFile

from ..models.manga import Manga
from ..models.capitulo import Capitulo
from ..models.pagina import Pagina
from ..exceptions import (
    MangaException, MangaValidationError, MangaNotFoundError, 
    ChapterNotFoundError, PageNotFoundError, DuplicateMangaError,
    DuplicateChapterError, DuplicatePageError, InvalidFileError,
    FileTooLargeError, UnsupportedFileTypeError, MangaPublishingError,
    ChapterPublishingError, PageProcessingError
)

User = get_user_model()

class IMangaService(ABC):
    """
    Interface para serviços de gerenciamento de mangás.
    
    Esta interface define os contratos que todas as implementações de serviço
    de mangá devem seguir, garantindo consistência e aderência aos princípios SOLID.
    """
    
    # Métodos para gerenciamento de mangás
    @abstractmethod
    def get_all_mangas(self, published_only: bool = True, **filters) -> QuerySet[Manga]:
        """
        Obtém todos os mangás, opcionalmente filtrados.
        
        Args:
            published_only: Se True, retorna apenas mangás publicados
            **filters: Filtros adicionais para a consulta
            
        Returns:
            QuerySet de mangás ordenados por data de criação (mais recentes primeiro)
            
        Raises:
            MangaException: Se ocorrer um erro ao buscar os mangás
        """
        pass
    
    @abstractmethod
    def get_manga_by_slug(self, slug: str) -> Manga:
        """
        Obtém um mangá pelo seu slug.
        
        Args:
            slug: Identificador único do mangá
            
        Returns:
            Instância do mangá encontrado
            
        Raises:
            MangaNotFoundError: Se o mangá não for encontrado
            MangaException: Se ocorrer outro erro durante a busca
        """
        pass
    
    @abstractmethod
    def search_mangas(self, query: str, **filters) -> QuerySet[Manga]:
        """
        Busca mangás por termo de busca.
        
        Args:
            query: Termo de busca (busca no título e descrição)
            **filters: Filtros adicionais para a consulta
            
        Returns:
            QuerySet de mangás que correspondem à busca
            
        Raises:
            MangaException: Se ocorrer um erro durante a busca
        """
        pass
    
    @abstractmethod
    def create_manga(self, manga_data: Dict[str, Any], created_by: User) -> Manga:
        """
        Cria um novo mangá.
        
        Args:
            manga_data: Dicionário com os dados do mangá
            created_by: Usuário que está criando o mangá
            
        Returns:
            Instância do mangá criado
            
        Raises:
            MangaValidationError: Se os dados do mangá forem inválidos
            DuplicateMangaError: Se já existir um mangá com o mesmo título
            MangaException: Se ocorrer outro erro durante a criação
        """
        pass
    
    @abstractmethod
    def update_manga(self, slug: str, manga_data: Dict[str, Any], updated_by: User) -> Manga:
        """
        Atualiza um mangá existente.
        
        Args:
            slug: Slug do mangá a ser atualizado
            manga_data: Dicionário com os dados atualizados
            updated_by: Usuário que está atualizando o mangá
            
        Returns:
            Instância do mangá atualizado
            
        Raises:
            MangaNotFoundError: Se o mangá não for encontrado
            MangaValidationError: Se os dados forem inválidos
            DuplicateMangaError: Se a atualização resultar em título duplicado
            MangaException: Se ocorrer outro erro durante a atualização
        """
        pass
    
    @abstractmethod
    def delete_manga(self, slug: str, deleted_by: User) -> bool:
        """
        Remove um mangá do sistema (exclusão lógica).
        
        Args:
            slug: Slug do mangá a ser removido
            deleted_by: Usuário que está removendo o mangá
            
        Returns:
            True se o mangá foi removido com sucesso
            
        Raises:
            MangaNotFoundError: Se o mangá não for encontrado
            MangaException: Se ocorrer um erro durante a remoção
        """
        pass
    
    @abstractmethod
    def publish_manga(self, slug: str, published: bool = True) -> Manga:
        """
        Publica ou despublica um mangá.
        
        Args:
            slug: Slug do mangá
            published: Se True, publica o mangá; se False, despublica
            
        Returns:
            Instância do mangá atualizado
            
        Raises:
            MangaNotFoundError: Se o mangá não for encontrado
            MangaPublishingError: Se ocorrer um erro ao publicar/despublicar
        """
        pass

    # Métodos para gerenciamento de capítulos
    @abstractmethod
    def get_manga_chapters(self, manga_slug: str, published_only: bool = True) -> QuerySet[Capitulo]:
        """
        Obtém os capítulos de um mangá.
        
        Args:
            manga_slug: Slug do mangá
            published_only: Se True, retorna apenas capítulos publicados
            
        Returns:
            QuerySet de capítulos ordenados por número
            
        Raises:
            MangaNotFoundError: Se o mangá não for encontrado
            MangaException: Se ocorrer outro erro durante a busca
        """
        pass
    
    @abstractmethod
    def get_chapter_by_slug(self, manga_slug: str, chapter_slug: str) -> Capitulo:
        """
        Obtém um capítulo pelo seu slug.
        
        Args:
            manga_slug: Slug do mangá
            chapter_slug: Slug do capítulo
            
        Returns:
            Instância do capítulo encontrado
            
        Raises:
            MangaNotFoundError: Se o mangá não for encontrado
            ChapterNotFoundError: Se o capítulo não for encontrado
            MangaException: Se ocorrer outro erro durante a busca
        """
        pass
    
    @abstractmethod
    def create_chapter(
        self, 
        manga_slug: str, 
        chapter_data: Dict[str, Any], 
        created_by: User
    ) -> Capitulo:
        """
        Cria um novo capítulo para um mangá.
        
        Args:
            manga_slug: Slug do mangá
            chapter_data: Dicionário com os dados do capítulo
            created_by: Usuário que está criando o capítulo
            
        Returns:
            Instância do capítulo criado
            
        Raises:
            MangaNotFoundError: Se o mangá não for encontrado
            MangaValidationError: Se os dados do capítulo forem inválidos
            DuplicateChapterError: Se já existir um capítulo com o mesmo número
            MangaException: Se ocorrer outro erro durante a criação
        """
        pass
    
    @abstractmethod
    def update_chapter(
        self, 
        manga_slug: str, 
        chapter_slug: str, 
        chapter_data: Dict[str, Any], 
        updated_by: User
    ) -> Capitulo:
        """
        Atualiza um capítulo existente.
        
        Args:
            manga_slug: Slug do mangá
            chapter_slug: Slug do capítulo a ser atualizado
            chapter_data: Dicionário com os dados atualizados
            updated_by: Usuário que está atualizando o capítulo
            
        Returns:
            Instância do capítulo atualizado
            
        Raises:
            MangaNotFoundError: Se o mangá não for encontrado
            ChapterNotFoundError: Se o capítulo não for encontrado
            MangaValidationError: Se os dados forem inválidos
            DuplicateChapterError: Se a atualização resultar em número de capítulo duplicado
            MangaException: Se ocorrer outro erro durante a atualização
        """
        pass
    
    @abstractmethod
    def delete_chapter(self, manga_slug: str, chapter_slug: str, deleted_by: User) -> bool:
        """
        Remove um capítulo do sistema.
        
        Args:
            manga_slug: Slug do mangá
            chapter_slug: Slug do capítulo a ser removido
            deleted_by: Usuário que está removendo o capítulo
            
        Returns:
            True se o capítulo foi removido com sucesso
            
        Raises:
            MangaNotFoundError: Se o mangá não for encontrado
            ChapterNotFoundError: Se o capítulo não for encontrado
            MangaException: Se ocorrer um erro durante a remoção
        """
        pass
    
    @abstractmethod
    def publish_chapter(self, manga_slug: str, chapter_slug: str, published: bool = True) -> Capitulo:
        """
        Publica ou despublica um capítulo.
        
        Args:
            manga_slug: Slug do mangá
            chapter_slug: Slug do capítulo
            published: Se True, publica o capítulo; se False, despublica
            
        Returns:
            Instância do capítulo atualizado
            
        Raises:
            MangaNotFoundError: Se o mangá não for encontrado
            ChapterNotFoundError: Se o capítulo não for encontrado
            ChapterPublishingError: Se ocorrer um erro ao publicar/despublicar
        """
        pass

    # Métodos para gerenciamento de páginas
    @abstractmethod
    def get_chapter_pages(self, manga_slug: str, chapter_slug: str) -> QuerySet[Pagina]:
        """
        Obtém as páginas de um capítulo.
        
        Args:
            manga_slug: Slug do mangá
            chapter_slug: Slug do capítulo
            
        Returns:
            QuerySet de páginas ordenadas por número
            
        Raises:
            MangaNotFoundError: Se o mangá não for encontrado
            ChapterNotFoundError: Se o capítulo não for encontrado
            MangaException: Se ocorrer outro erro durante a busca
        """
        pass
    
    @abstractmethod
    def get_page(self, manga_slug: str, chapter_slug: str, page_number: int) -> Pagina:
        """
        Obtém uma página específica de um capítulo.
        
        Args:
            manga_slug: Slug do mangá
            chapter_slug: Slug do capítulo
            page_number: Número da página
            
        Returns:
            Instância da página encontrada
            
        Raises:
            MangaNotFoundError: Se o mangá não for encontrado
            ChapterNotFoundError: Se o capítulo não for encontrado
            PageNotFoundError: Se a página não for encontrada
            MangaException: Se ocorrer outro erro durante a busca
        """
        pass
    
    @abstractmethod
    def add_page(
        self, 
        manga_slug: str, 
        chapter_slug: str, 
        image_file: UploadedFile, 
        created_by: User,
        page_number: Optional[int] = None
    ) -> Pagina:
        """
        Adiciona uma nova página a um capítulo.
        
        Args:
            manga_slug: Slug do mangá
            chapter_slug: Slug do capítulo
            image_file: Arquivo de imagem da página
            created_by: Usuário que está adicionando a página
            page_number: Número opcional da página (se None, será o próximo disponível)
            
        Returns:
            Instância da página criada
            
        Raises:
            MangaNotFoundError: Se o mangá não for encontrado
            ChapterNotFoundError: Se o capítulo não for encontrado
            InvalidFileError: Se o arquivo de imagem for inválido
            FileTooLargeError: Se o arquivo exceder o tamanho máximo permitido
            UnsupportedFileTypeError: Se o tipo de arquivo não for suportado
            DuplicatePageError: Se já existir uma página com o mesmo número
            PageProcessingError: Se ocorrer um erro ao processar a imagem
            MangaException: Se ocorrer outro erro durante a criação
        """
        pass
    
    @abstractmethod
    def update_page(
        self, 
        manga_slug: str, 
        chapter_slug: str, 
        page_number: int, 
        image_file: UploadedFile, 
        updated_by: User
    ) -> Pagina:
        """
        Atualiza uma página existente.
        
        Args:
            manga_slug: Slug do mangá
            chapter_slug: Slug do capítulo
            page_number: Número da página a ser atualizada
            image_file: Novo arquivo de imagem
            updated_by: Usuário que está atualizando a página
            
        Returns:
            Instância da página atualizada
            
        Raises:
            MangaNotFoundError: Se o mangá não for encontrado
            ChapterNotFoundError: Se o capítulo não for encontrado
            PageNotFoundError: Se a página não for encontrada
            InvalidFileError: Se o arquivo de imagem for inválido
            FileTooLargeError: Se o arquivo exceder o tamanho máximo permitido
            UnsupportedFileTypeError: Se o tipo de arquivo não for suportado
            PageProcessingError: Se ocorrer um erro ao processar a imagem
            MangaException: Se ocorrer outro erro durante a atualização
        """
        pass
    
    @abstractmethod
    def delete_page(self, manga_slug: str, chapter_slug: str, page_number: int, deleted_by: User) -> bool:
        """
        Remove uma página de um capítulo.
        
        Args:
            manga_slug: Slug do mangá
            chapter_slug: Slug do capítulo
            page_number: Número da página a ser removida
            deleted_by: Usuário que está removendo a página
            
        Returns:
            True se a página foi removida com sucesso
            
        Raises:
            MangaNotFoundError: Se o mangá não for encontrado
            ChapterNotFoundError: Se o capítulo não for encontrado
            PageNotFoundError: Se a página não for encontrada
            MangaException: Se ocorrer um erro durante a remoção
        """
        pass
    
    @abstractmethod
    def reorder_pages(
        self, 
        manga_slug: str, 
        chapter_slug: str, 
        new_order: Dict[int, int],
        updated_by: User
    ) -> bool:
        """
        Reordena as páginas de um capítulo.
        
        Args:
            manga_slug: Slug do mangá
            chapter_slug: Slug do capítulo
            new_order: Dicionário mapeando números de página antigos para novos
            updated_by: Usuário que está reordenando as páginas
            
        Returns:
            True se a reordenação foi bem-sucedida
            
        Raises:
            MangaNotFoundError: Se o mangá não for encontrado
            ChapterNotFoundError: Se o capítulo não for encontrado
            MangaValidationError: Se a nova ordem for inválida
            MangaException: Se ocorrer um erro durante a reordenação
        """
        pass