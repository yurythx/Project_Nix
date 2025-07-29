"""
Implementação simplificada e funcional do serviço de mangás
Segue princípios SOLID e foca na funcionalidade essencial
Agora com cache inteligente integrado
"""

import logging
from typing import Dict, Any, Optional
from django.db import models
from django.db.models import QuerySet, Count, F
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.uploadedfile import UploadedFile

from ..interfaces.services import IMangaService
from ..repositories.manga_repository import DjangoMangaRepository
from ..services.cache_service import manga_cache
from ..services.logging_service import manga_logger, log_performance
from ..models.manga import Manga
from ..models.capitulo import Capitulo
from ..exceptions import MangaNotFoundError, MangaValidationError

logger = logging.getLogger(__name__)


class SimpleMangaService(IMangaService):
    """
    Implementação simplificada e funcional do serviço de mangás
    
    Princípios SOLID aplicados:
    - Single Responsibility: Apenas lógica de negócio de mangás
    - Dependency Inversion: Usa repository através de interface
    - Open/Closed: Extensível sem modificar código base
    """
    
    def __init__(self, repository=None):
        """
        Inicializa service com injeção de dependência

        Args:
            repository: Repository de mangás (opcional)
        """
        self.repository = repository or DjangoMangaRepository()
        self.logger = logger
        self.manga_logger = manga_logger
    
    def get_all_mangas(self, published_only: bool = True, **filters) -> QuerySet[Manga]:
        """
        Obtém todos os mangás com filtros opcionais
        
        Args:
            published_only: Se True, retorna apenas mangás publicados
            **filters: Filtros adicionais
            
        Returns:
            QuerySet de mangás
        """
        try:
            if published_only:
                return self.repository.get_published_mangas()
            return Manga.objects.all()
        except Exception as e:
            self.logger.error(f"Erro ao buscar mangás: {e}")
            raise MangaValidationError(f"Erro ao buscar mangás: {str(e)}")
    
    @log_performance("get_manga_by_slug")
    def get_manga_by_slug(self, slug: str) -> Manga:
        """
        Obtém mangá por slug com cache inteligente

        Args:
            slug: Slug do mangá

        Returns:
            Manga encontrado

        Raises:
            MangaNotFoundError: Se não encontrado
        """
        # Tenta buscar no cache primeiro
        cached_data = manga_cache.get_cached_manga(slug)
        if cached_data:
            try:
                # Reconstrói objeto Manga a partir do cache
                manga = Manga.objects.get(id=cached_data['id'])
                return manga
            except Manga.DoesNotExist:
                # Cache inválido, remove
                manga_cache.invalidate_manga_cache(slug)

        # Busca no banco de dados
        manga = self.repository.get_by_slug(slug)
        if not manga:
            raise MangaNotFoundError(f"Mangá '{slug}' não encontrado")

        # Armazena no cache
        manga_cache.cache_manga(manga)

        return manga
    
    def get_manga_context(self, manga: Manga) -> Dict[str, Any]:
        """
        Retorna contexto completo para templates com cache

        Args:
            manga: Instância do mangá

        Returns:
            Dicionário com contexto
        """
        try:
            # Tenta buscar contexto no cache
            cached_context = manga_cache.get_cached_manga_context(manga.slug)
            if cached_context:
                # Reconstrói objetos a partir dos IDs cachados
                context = {
                    'total_chapters': cached_context['total_chapters'],
                    'chapter_count': cached_context['chapter_count'],
                    'volumes_count': cached_context['volumes_count'],
                }

                # Busca latest_chapter se existe
                if cached_context.get('latest_chapter_id'):
                    try:
                        context['latest_chapter'] = Capitulo.objects.get(
                            id=cached_context['latest_chapter_id']
                        )
                    except Capitulo.DoesNotExist:
                        context['latest_chapter'] = None
                else:
                    context['latest_chapter'] = None

                # Volumes são buscados sempre (podem ter mudado)
                context['volumes'] = manga.volumes.prefetch_related('capitulos').all()

                return context

            # Gera contexto completo
            context = {
                'volumes': manga.volumes.prefetch_related('capitulos').all(),
                'total_chapters': self._get_total_chapters(manga),
                'latest_chapter': self._get_latest_chapter(manga),
                'chapter_count': manga.volumes.aggregate(
                    total=Count('capitulos')
                ).get('total', 0),
            }

            # Armazena no cache
            manga_cache.cache_manga_context(manga.slug, context)

            return context

        except Exception as e:
            self.logger.error(f"Erro ao obter contexto do manga {manga.slug}: {e}")
            return {}
    
    def get_chapter_context(self, chapter: Capitulo) -> Dict[str, Any]:
        """
        Retorna contexto de navegação para capítulo
        
        Args:
            chapter: Instância do capítulo
            
        Returns:
            Dicionário com contexto de navegação
        """
        try:
            manga = chapter.volume.manga
            all_chapters = Capitulo.objects.filter(
                volume__manga=manga,
                is_published=True
            ).order_by('volume__number', 'number')
            
            current_index = None
            for i, ch in enumerate(all_chapters):
                if ch.id == chapter.id:
                    current_index = i
                    break
            
            previous_chapter = None
            next_chapter = None
            
            if current_index is not None:
                if current_index > 0:
                    previous_chapter = all_chapters[current_index - 1]
                if current_index < len(all_chapters) - 1:
                    next_chapter = all_chapters[current_index + 1]
            
            return {
                'previous_chapter': previous_chapter,
                'next_chapter': next_chapter,
                'pages': chapter.paginas.all().order_by('number'),
                'total_pages': chapter.paginas.count(),
            }
        except Exception as e:
            self.logger.error(f"Erro ao obter contexto do capítulo {chapter.slug}: {e}")
            return {}
    
    def increment_manga_views(self, manga_id: int) -> bool:
        """
        Incrementa visualizações do mangá
        
        Args:
            manga_id: ID do mangá
            
        Returns:
            True se incrementado com sucesso
        """
        try:
            Manga.objects.filter(id=manga_id).update(
                view_count=F('view_count') + 1
            )
            return True
        except Exception as e:
            self.logger.error(f"Erro ao incrementar views do manga {manga_id}: {e}")
            return False
    
    def search_mangas(self, query: str, **filters) -> QuerySet[Manga]:
        """
        Busca mangás por termo
        
        Args:
            query: Termo de busca
            **filters: Filtros adicionais
            
        Returns:
            QuerySet de mangás encontrados
        """
        return self.repository.search_mangas(query, **filters)
    
    def get_featured_mangas(self, limit: int = 5) -> QuerySet[Manga]:
        """
        Obtém mangás em destaque
        
        Args:
            limit: Número máximo de mangás
            
        Returns:
            QuerySet de mangás em destaque
        """
        return self.repository.get_published_mangas().filter(
            is_featured=True
        )[:limit]
    
    def _get_total_chapters(self, manga: Manga) -> int:
        """Retorna total de capítulos do mangá"""
        return Capitulo.objects.filter(volume__manga=manga).count()
    
    def _get_latest_chapter(self, manga: Manga) -> Optional[Capitulo]:
        """Retorna último capítulo do mangá"""
        return Capitulo.objects.filter(
            volume__manga=manga,
            is_published=True
        ).order_by('-volume__number', '-number').first()
    
    # Implementação mínima dos métodos da interface
    def create_manga(self, manga_data: Dict[str, Any], created_by: User) -> Manga:
        """Cria novo mangá"""
        return self.repository.create(manga_data, created_by)
    
    def update_manga(self, slug: str, manga_data: Dict[str, Any]) -> Manga:
        """Atualiza mangá existente"""
        manga = self.get_manga_by_slug(slug)
        return self.repository.update(manga, manga_data)
    
    def delete_manga(self, slug: str) -> None:
        """Remove mangá"""
        manga = self.get_manga_by_slug(slug)
        self.repository.delete(manga)
    
    # Métodos não implementados da interface (para compatibilidade)
    def get_manga_chapters(self, manga_slug: str, published_only: bool = True) -> QuerySet[Capitulo]:
        """Obtém capítulos do mangá"""
        manga = self.get_manga_by_slug(manga_slug)
        chapters = Capitulo.objects.filter(volume__manga=manga)
        if published_only:
            chapters = chapters.filter(is_published=True)
        return chapters.order_by('volume__number', 'number')
    
    def get_chapter_by_slug(self, manga_slug: str, chapter_slug: str) -> Capitulo:
        """Obtém capítulo por slug"""
        manga = self.get_manga_by_slug(manga_slug)
        try:
            return Capitulo.objects.get(volume__manga=manga, slug=chapter_slug)
        except Capitulo.DoesNotExist:
            raise MangaNotFoundError(f"Capítulo '{chapter_slug}' não encontrado")
    
    def create_chapter(self, manga_slug: str, chapter_data: Dict[str, Any], created_by: User) -> Capitulo:
        """Cria novo capítulo"""
        manga = self.get_manga_by_slug(manga_slug)
        chapter_data['created_by'] = created_by
        # Implementação básica - pode ser expandida
        return Capitulo.objects.create(**chapter_data)
    
    def update_chapter(self, manga_slug: str, chapter_slug: str, chapter_data: Dict[str, Any]) -> Capitulo:
        """Atualiza capítulo existente"""
        chapter = self.get_chapter_by_slug(manga_slug, chapter_slug)
        for key, value in chapter_data.items():
            setattr(chapter, key, value)
        chapter.save()
        return chapter
    
    def delete_chapter(self, manga_slug: str, chapter_slug: str) -> None:
        """Remove capítulo"""
        chapter = self.get_chapter_by_slug(manga_slug, chapter_slug)
        chapter.delete()
    
    def publish_manga(self, slug: str, published: bool = True) -> Manga:
        """Publica/despublica mangá"""
        manga = self.get_manga_by_slug(slug)
        manga.is_published = published
        manga.save()
        return manga
    
    def publish_chapter(self, manga_slug: str, chapter_slug: str, published: bool = True) -> Capitulo:
        """Publica/despublica capítulo"""
        chapter = self.get_chapter_by_slug(manga_slug, chapter_slug)
        chapter.is_published = published
        chapter.save()
        return chapter

    # === MÉTODOS DE PÁGINAS (IMPLEMENTAÇÃO BÁSICA) ===

    def get_chapter_pages(self, manga_slug: str, chapter_slug: str) -> QuerySet:
        """Obtém páginas do capítulo"""
        from ..models.pagina import Pagina
        chapter = self.get_chapter_by_slug(manga_slug, chapter_slug)
        return Pagina.objects.filter(capitulo=chapter).order_by('number')

    def get_page(self, manga_slug: str, chapter_slug: str, page_number: int):
        """Obtém página específica"""
        from ..models.pagina import Pagina
        chapter = self.get_chapter_by_slug(manga_slug, chapter_slug)
        try:
            return Pagina.objects.get(capitulo=chapter, number=page_number)
        except Pagina.DoesNotExist:
            raise MangaNotFoundError(f"Página {page_number} não encontrada")

    def add_page(self, manga_slug: str, chapter_slug: str, image_file, created_by: User, **kwargs):
        """Adiciona nova página"""
        from ..models.pagina import Pagina
        chapter = self.get_chapter_by_slug(manga_slug, chapter_slug)

        # Determina próximo número
        last_page = Pagina.objects.filter(capitulo=chapter).order_by('-number').first()
        next_number = (last_page.number + 1) if last_page else 1

        page_data = {
            'capitulo': chapter,
            'number': kwargs.get('page_number', next_number),
            'image': image_file,
            'alt_text': kwargs.get('alt_text', ''),
            'created_by': created_by
        }

        return Pagina.objects.create(**page_data)

    def update_page(self, manga_slug: str, chapter_slug: str, page_number: int, image_file, updated_by: User, **kwargs):
        """Atualiza página existente"""
        page = self.get_page(manga_slug, chapter_slug, page_number)

        if image_file:
            page.image = image_file

        if 'alt_text' in kwargs:
            page.alt_text = kwargs['alt_text']

        page.save()
        return page

    def delete_page(self, manga_slug: str, chapter_slug: str, page_number: int, deleted_by: User) -> bool:
        """Remove página"""
        try:
            page = self.get_page(manga_slug, chapter_slug, page_number)
            page.delete()
            return True
        except Exception as e:
            self.logger.error(f"Erro ao deletar página: {e}")
            return False

    def reorder_pages(self, manga_slug: str, chapter_slug: str, new_order: Dict[int, int], updated_by: User) -> bool:
        """Reordena páginas do capítulo"""
        try:
            from ..models.pagina import Pagina
            chapter = self.get_chapter_by_slug(manga_slug, chapter_slug)

            for old_number, new_number in new_order.items():
                Pagina.objects.filter(
                    capitulo=chapter,
                    number=old_number
                ).update(number=new_number)

            return True
        except Exception as e:
            self.logger.error(f"Erro ao reordenar páginas: {e}")
            return False
