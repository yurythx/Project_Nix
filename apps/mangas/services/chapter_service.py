"""Service dedicado para operações de capítulos
Refatoração para simplificar views complexas"""

import logging
from typing import Dict, Any, Optional, List
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import QuerySet
from django.contrib.auth.models import User

from ..models.capitulo import Capitulo
from ..models.pagina import Pagina
from ..exceptions import ChapterNotFoundError

logger = logging.getLogger(__name__)

class ChapterService:
    """Service para operações específicas de capítulos"""
    
    def get_chapter_by_slug(self, manga_slug: str, chapter_slug: str, user: Optional[User] = None) -> Capitulo:
        """Obtém capítulo por slug com verificações de permissão"""
        try:
            queryset = Capitulo.objects.select_related('volume__manga').prefetch_related('paginas')
            
            # Filtra por publicação se usuário não é staff
            if not user or not (user.is_authenticated and user.is_staff):
                queryset = queryset.filter(is_published=True)
            
            return queryset.get(
                slug=chapter_slug,
                volume__manga__slug=manga_slug
            )
        except Capitulo.DoesNotExist:
            raise ChapterNotFoundError(f"Capítulo '{chapter_slug}' não encontrado")
    
    def get_chapter_navigation(self, chapter: Capitulo) -> Dict[str, Optional[Capitulo]]:
        """Obtém capítulos anterior e próximo para navegação"""
        try:
            # Obtém todos os capítulos do mangá ordenados
            all_chapters = Capitulo.objects.filter(
                volume__manga=chapter.volume.manga,
                is_published=True
            ).select_related('volume').order_by('volume__number', 'number')
            
            chapters_list = list(all_chapters)
            current_index = None
            
            # Encontra o índice do capítulo atual
            for i, cap in enumerate(chapters_list):
                if cap.id == chapter.id:
                    current_index = i
                    break
            
            if current_index is None:
                return {'previous_chapter': None, 'next_chapter': None}
            
            # Determina capítulos anterior e próximo
            previous_chapter = chapters_list[current_index - 1] if current_index > 0 else None
            next_chapter = chapters_list[current_index + 1] if current_index < len(chapters_list) - 1 else None
            
            return {
                'previous_chapter': previous_chapter,
                'next_chapter': next_chapter
            }
        except Exception as e:
            logger.error(f"Erro ao obter navegação do capítulo {chapter.id}: {e}")
            return {'previous_chapter': None, 'next_chapter': None}
    
    def get_chapter_pages_paginated(self, chapter: Capitulo, page_number: str = '1', per_page: int = 1) -> Dict[str, Any]:
        """Obtém páginas do capítulo com paginação"""
        try:
            pages = chapter.paginas.all().order_by('number')
            paginator = Paginator(pages, per_page)
            
            try:
                paginated_pages = paginator.page(page_number)
            except PageNotAnInteger:
                paginated_pages = paginator.page(1)
            except EmptyPage:
                paginated_pages = paginator.page(paginator.num_pages)
            
            return {
                'pages': paginated_pages,
                'total_pages': paginator.count,
                'current_page_number': paginated_pages.number,
                'has_previous': paginated_pages.has_previous(),
                'has_next': paginated_pages.has_next(),
                'previous_page_number': paginated_pages.previous_page_number() if paginated_pages.has_previous() else None,
                'next_page_number': paginated_pages.next_page_number() if paginated_pages.has_next() else None,
            }
        except Exception as e:
            logger.error(f"Erro ao paginar páginas do capítulo {chapter.id}: {e}")
            return {
                'pages': [],
                'total_pages': 0,
                'current_page_number': 1,
                'has_previous': False,
                'has_next': False,
                'previous_page_number': None,
                'next_page_number': None,
            }
    
    def get_complete_chapter_context(self, chapter: Capitulo, page_number: str = '1', user: Optional[User] = None) -> Dict[str, Any]:
        """Obtém contexto completo do capítulo para views"""
        try:
            # Navegação entre capítulos
            navigation = self.get_chapter_navigation(chapter)
            
            # Paginação das páginas
            pagination = self.get_chapter_pages_paginated(chapter, page_number)
            
            # Volumes do mangá para navegação
            volumes = chapter.volume.manga.volumes.all().order_by('number')
            
            return {
                **navigation,
                **pagination,
                'volumes': volumes,
                'manga': chapter.volume.manga,
                'volume': chapter.volume,
            }
        except Exception as e:
            logger.error(f"Erro ao obter contexto completo do capítulo {chapter.id}: {e}")
            raise ChapterNotFoundError(f"Erro ao processar capítulo: {str(e)}")
    
    def increment_chapter_views(self, chapter: Capitulo) -> None:
        """Incrementa visualizações do capítulo e do mangá"""
        try:
            # Incrementa views do mangá (não do capítulo individual)
            manga = chapter.volume.manga
            manga.view_count += 1
            manga.save(update_fields=['view_count'])
            
            logger.info(f"Views incrementadas para mangá {manga.slug}")
        except Exception as e:
            logger.warning(f"Erro ao incrementar views do capítulo {chapter.id}: {e}")