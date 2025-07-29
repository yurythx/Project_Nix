"""
Interfaces para repositories do app mangas
Implementa o princípio Dependency Inversion do SOLID
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from django.db.models import QuerySet
from django.contrib.auth.models import User

from ..models.manga import Manga
from ..models.capitulo import Capitulo
from ..models.pagina import Pagina
from ..models.volume import Volume


class IMangaRepository(ABC):
    """
    Interface para repository de mangás
    
    Princípios SOLID aplicados:
    - Interface Segregation: Interface específica para mangás
    - Dependency Inversion: Abstrações não dependem de detalhes
    """
    
    @abstractmethod
    def get_by_slug(self, slug: str) -> Optional[Manga]:
        """Busca mangá por slug"""
        pass
    
    @abstractmethod
    def get_published_mangas(self) -> QuerySet[Manga]:
        """Retorna mangás publicados com otimizações"""
        pass
    
    @abstractmethod
    def get_manga_with_chapters(self, slug: str) -> Optional[Manga]:
        """Retorna mangá com capítulos pré-carregados"""
        pass
    
    @abstractmethod
    def get_manga_with_full_data(self, slug: str) -> Optional[Manga]:
        """Retorna mangá com todos os dados relacionados"""
        pass
    
    @abstractmethod
    def search_mangas(self, query: str, **filters) -> QuerySet[Manga]:
        """Busca mangás por termo"""
        pass
    
    @abstractmethod
    def create(self, manga_data: Dict[str, Any], user: User) -> Manga:
        """Cria novo mangá"""
        pass
    
    @abstractmethod
    def update(self, manga: Manga, manga_data: Dict[str, Any]) -> Manga:
        """Atualiza mangá existente"""
        pass
    
    @abstractmethod
    def delete(self, manga: Manga) -> bool:
        """Remove mangá"""
        pass


class IChapterRepository(ABC):
    """Interface para repository de capítulos"""
    
    @abstractmethod
    def get_by_slug(self, manga_slug: str, chapter_slug: str) -> Optional[Capitulo]:
        """Busca capítulo por slug"""
        pass
    
    @abstractmethod
    def get_chapter_with_pages(self, manga_slug: str, chapter_slug: str) -> Optional[Capitulo]:
        """Retorna capítulo com páginas pré-carregadas"""
        pass
    
    @abstractmethod
    def get_manga_chapters(self, manga: Manga, published_only: bool = True) -> QuerySet[Capitulo]:
        """Retorna capítulos do mangá"""
        pass
    
    @abstractmethod
    def get_navigation_context(self, chapter: Capitulo) -> Dict[str, Optional[Capitulo]]:
        """Retorna contexto de navegação (anterior/próximo)"""
        pass
    
    @abstractmethod
    def create(self, manga: Manga, chapter_data: Dict[str, Any], user: User) -> Capitulo:
        """Cria novo capítulo"""
        pass
    
    @abstractmethod
    def update(self, chapter: Capitulo, chapter_data: Dict[str, Any]) -> Capitulo:
        """Atualiza capítulo existente"""
        pass
    
    @abstractmethod
    def delete(self, chapter: Capitulo) -> bool:
        """Remove capítulo"""
        pass


class IPageRepository(ABC):
    """Interface para repository de páginas"""
    
    @abstractmethod
    def get_chapter_pages(self, chapter: Capitulo) -> QuerySet[Pagina]:
        """Retorna páginas do capítulo ordenadas"""
        pass
    
    @abstractmethod
    def get_page_by_number(self, chapter: Capitulo, page_number: int) -> Optional[Pagina]:
        """Busca página por número"""
        pass
    
    @abstractmethod
    def create(self, chapter: Capitulo, page_data: Dict[str, Any], user: User) -> Pagina:
        """Cria nova página"""
        pass
    
    @abstractmethod
    def update(self, page: Pagina, page_data: Dict[str, Any]) -> Pagina:
        """Atualiza página existente"""
        pass
    
    @abstractmethod
    def delete(self, page: Pagina) -> bool:
        """Remove página"""
        pass
    
    @abstractmethod
    def reorder_pages(self, chapter: Capitulo, new_order: Dict[int, int]) -> bool:
        """Reordena páginas do capítulo"""
        pass


class IVolumeRepository(ABC):
    """Interface para repository de volumes"""
    
    @abstractmethod
    def get_by_id(self, volume_id: int) -> Optional[Volume]:
        """Busca volume por ID"""
        pass
    
    @abstractmethod
    def get_manga_volumes(self, manga: Manga) -> QuerySet[Volume]:
        """Retorna volumes do mangá"""
        pass
    
    @abstractmethod
    def get_volume_with_chapters(self, volume_id: int) -> Optional[Volume]:
        """Retorna volume com capítulos pré-carregados"""
        pass
    
    @abstractmethod
    def create(self, manga: Manga, volume_data: Dict[str, Any], user: User) -> Volume:
        """Cria novo volume"""
        pass
    
    @abstractmethod
    def update(self, volume: Volume, volume_data: Dict[str, Any]) -> Volume:
        """Atualiza volume existente"""
        pass
    
    @abstractmethod
    def delete(self, volume: Volume) -> bool:
        """Remove volume"""
        pass
