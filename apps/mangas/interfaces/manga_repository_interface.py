from abc import ABC, abstractmethod
from typing import List, Optional
from django.db.models import QuerySet

from ..models.manga import Manga
from ..models.capitulo import Capitulo
from ..models.pagina import Pagina

class MangaRepositoryInterface(ABC):
    """
    Interface para repositório de mangás.

    Define os contratos que todas as implementações de repositório
    devem seguir, garantindo consistência e aderência aos princípios SOLID.

    Exemplo de uso:
        >>> from apps.mangas.repositories.manga_repository import MangaRepository
        >>> repo = MangaRepository()
        >>> mangas = repo.list_mangas()
        >>> manga = repo.get_manga_by_slug('naruto')
    """

    @abstractmethod
    def list_mangas(self) -> QuerySet[Manga]:
        """Lista todos os mangás."""
        pass

    @abstractmethod
    def get_manga_by_slug(self, slug: str) -> Manga:
        """Obtém um mangá pelo slug."""
        pass

    @abstractmethod
    def create_manga(self, data: dict) -> Manga:
        """Cria um novo mangá."""
        pass

    @abstractmethod
    def update_manga(self, slug: str, data: dict) -> Manga:
        """Atualiza um mangá existente."""
        pass

    @abstractmethod
    def delete_manga(self, slug: str) -> None:
        """Exclui um mangá."""
        pass

    @abstractmethod
    def list_capitulos(self, manga: Manga) -> QuerySet[Capitulo]:
        """Lista todos os capítulos de um mangá."""
        pass

    @abstractmethod
    def get_capitulo_by_slug(self, manga: Manga, capitulo_slug: str) -> Capitulo:
        """Obtém um capítulo pelo slug."""
        pass

    @abstractmethod
    def create_capitulo(self, manga: Manga, data: dict) -> Capitulo:
        """Cria um novo capítulo."""
        pass

    @abstractmethod
    def update_capitulo(self, manga: Manga, capitulo_slug: str, data: dict) -> Capitulo:
        """Atualiza um capítulo existente."""
        pass

    @abstractmethod
    def delete_capitulo(self, manga: Manga, capitulo_slug: str) -> None:
        """Exclui um capítulo."""
        pass

    @abstractmethod
    def list_paginas(self, capitulo: Capitulo) -> QuerySet[Pagina]:
        """Lista todas as páginas de um capítulo."""
        pass

    @abstractmethod
    def get_pagina(self, capitulo: Capitulo, number: int) -> Pagina:
        """Obtém uma página pelo número."""
        pass

    @abstractmethod
    def create_pagina(self, capitulo: Capitulo, data: dict) -> Pagina:
        """Cria uma nova página."""
        pass

    @abstractmethod
    def update_pagina(self, capitulo: Capitulo, number: int, data: dict) -> Pagina:
        """Atualiza uma página existente."""
        pass

    @abstractmethod
    def delete_pagina(self, capitulo: Capitulo, number: int) -> None:
        """Exclui uma página."""
        pass 