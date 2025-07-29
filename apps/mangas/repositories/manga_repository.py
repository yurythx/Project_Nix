"""
Implementação concreta do repository de mangás usando Django ORM
Segue princípios SOLID e otimiza queries para performance
"""
import logging
from typing import Optional, Dict, Any
from django.db.models import QuerySet, Q, Prefetch
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from ..interfaces.repositories import IMangaRepository
from ..models.manga import Manga
from ..models.capitulo import Capitulo
from ..models.pagina import Pagina
from ..exceptions import MangaNotFoundError, MangaValidationError

logger = logging.getLogger(__name__)


class DjangoMangaRepository(IMangaRepository):
    """
    Implementação Django do repository de mangás

    Princípios SOLID aplicados:
    - Single Responsibility: Apenas acesso a dados de mangás
    - Dependency Inversion: Implementa interface abstrata
    - Open/Closed: Extensível sem modificar código base
    """

    def get_by_slug(self, slug: str) -> Optional[Manga]:
        """
        Busca mangá por slug com otimizações básicas

        Args:
            slug: Slug do mangá

        Returns:
            Manga encontrado ou None
        """
        try:
            return Manga.objects.select_related('created_by').get(
                slug=slug,
                is_published=True
            )
        except Manga.DoesNotExist:
            logger.warning(f"Manga não encontrado: {slug}")
            return None

    def get_published_mangas(self) -> QuerySet[Manga]:
        """
        Retorna mangás publicados com otimizações de performance

        Returns:
            QuerySet otimizado de mangás publicados
        """
        return Manga.objects.filter(
            is_published=True,
            status='published'
        ).select_related('created_by').prefetch_related(
            'volumes'
        ).order_by('-created_at')

    def get_manga_with_chapters(self, slug: str) -> Optional[Manga]:
        """
        Retorna mangá com capítulos pré-carregados (resolve N+1)

        Args:
            slug: Slug do mangá

        Returns:
            Manga com capítulos ou None
        """
        try:
            return Manga.objects.select_related('created_by').prefetch_related(
                'volumes__capitulos'
            ).get(slug=slug)
        except Manga.DoesNotExist:
            logger.warning(f"Manga com capítulos não encontrado: {slug}")
            return None

    def get_manga_with_full_data(self, slug: str) -> Optional[Manga]:
        """
        Retorna mangá com todos os dados relacionados (para views complexas)

        Args:
            slug: Slug do mangá

        Returns:
            Manga com dados completos ou None
        """
        try:
            # Prefetch otimizado para evitar N+1 queries
            capitulos_prefetch = Prefetch(
                'volumes__capitulos',
                queryset=Capitulo.objects.select_related('volume').prefetch_related('paginas')
            )

            return Manga.objects.select_related('created_by').prefetch_related(
                'volumes',
                capitulos_prefetch
            ).get(slug=slug)
        except Manga.DoesNotExist:
            logger.warning(f"Manga com dados completos não encontrado: {slug}")
            return None

    def search_mangas(self, query: str, **filters) -> QuerySet[Manga]:
        """
        Busca mangás por termo com filtros opcionais

        Args:
            query: Termo de busca
            **filters: Filtros adicionais

        Returns:
            QuerySet de mangás encontrados
        """
        queryset = self.get_published_mangas()

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(author__icontains=query)
            )

        # Aplicar filtros adicionais
        if 'author' in filters:
            queryset = queryset.filter(author__icontains=filters['author'])

        if 'status' in filters:
            queryset = queryset.filter(status=filters['status'])

        return queryset.distinct()

    def create(self, manga_data: Dict[str, Any], user: User) -> Manga:
        """
        Cria novo mangá

        Args:
            manga_data: Dados do mangá
            user: Usuário criador

        Returns:
            Manga criado

        Raises:
            MangaValidationError: Se dados inválidos
        """
        try:
            manga_data['created_by'] = user
            manga = Manga.objects.create(**manga_data)

            logger.info(f"Manga criado: {manga.title} por {user.username}")
            return manga

        except Exception as e:
            logger.error(f"Erro ao criar manga: {e}")
            raise MangaValidationError(f"Erro ao criar mangá: {str(e)}")

    def update(self, manga: Manga, manga_data: Dict[str, Any]) -> Manga:
        """
        Atualiza mangá existente

        Args:
            manga: Instância do mangá
            manga_data: Dados para atualização

        Returns:
            Manga atualizado

        Raises:
            MangaValidationError: Se dados inválidos
        """
        try:
            for key, value in manga_data.items():
                if hasattr(manga, key):
                    setattr(manga, key, value)

            manga.save()

            logger.info(f"Manga atualizado: {manga.title}")
            return manga

        except Exception as e:
            logger.error(f"Erro ao atualizar manga {manga.id}: {e}")
            raise MangaValidationError(f"Erro ao atualizar mangá: {str(e)}")

    def delete(self, manga: Manga) -> bool:
        """
        Remove mangá (exclusão lógica)

        Args:
            manga: Instância do mangá

        Returns:
            True se removido com sucesso
        """
        try:
            manga.is_published = False
            manga.status = 'deleted'
            manga.save()

            logger.info(f"Manga removido logicamente: {manga.title}")
            return True

        except Exception as e:
            logger.error(f"Erro ao remover manga {manga.id}: {e}")
            return False


# Manter compatibilidade com código existente
class MangaRepository(DjangoMangaRepository):
    """Alias para compatibilidade com código existente"""
    pass