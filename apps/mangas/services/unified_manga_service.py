import os
import logging
import zipfile
import rarfile
from typing import List, Dict, Optional, Tuple, Any, Union
from django.core.files.uploadedfile import UploadedFile
from django.core.cache import cache
from django.db import transaction, models
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.contrib.auth.models import User
from PIL import Image
import tempfile
import shutil

from apps.mangas.models import Manga, Volume, Capitulo, Pagina
from apps.mangas.interfaces.services import IMangaService
from apps.mangas.validators import (
    ImageFileValidator,
    ArchiveFileValidator
)
from apps.mangas.constants.file_limits import (
    CACHE_KEYS,
    MAX_PAGES_PER_CHAPTER,
    ALLOWED_IMAGE_EXTENSIONS,
    ERROR_MESSAGES
)
from apps.mangas.exceptions import (
    MangaException, MangaNotFoundError, MangaValidationError,
    DuplicateMangaError, ChapterNotFoundError, PageNotFoundError,
    DuplicateChapterError, DuplicatePageError, InvalidFileError,
    FileTooLargeError, UnsupportedFileTypeError
)

logger = logging.getLogger(__name__)

# Definir CACHE_TIMEOUT localmente (não existe no file_limits.py)
CACHE_TIMEOUT = 3600  # 1 hora

class UnifiedMangaService(IMangaService):
    """Serviço unificado para operações de mangá com cache inteligente."""
    
    def __init__(self, repository=None):
        """
        Inicializa o serviço com injeção de dependência opcional.
        
        Args:
            repository: Repositório opcional para acesso a dados (não utilizado nesta implementação)
        """
        self.cache_timeout = CACHE_TIMEOUT
        # Nesta implementação, não utilizamos o padrão de repositório,
        # mas mantemos o parâmetro para compatibilidade com a interface
    
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
        try:
            # Buscar no cache se não houver filtros adicionais
            if not filters and published_only:
                cached_mangas = cache.get('manga_list')
                if cached_mangas:
                    return cached_mangas
            
            # Construir queryset
            queryset = Manga.objects.all()
            
            # Aplicar filtro de publicação
            if published_only:
                queryset = queryset.filter(is_published=True)
            
            # Aplicar filtros adicionais
            if filters:
                queryset = queryset.filter(**filters)
            
            # Ordenar por data de criação (mais recentes primeiro)
            queryset = queryset.order_by('-created_at')
            
            # Armazenar no cache se não houver filtros adicionais
            if not filters and published_only:
                cache.set('manga_list', queryset, self.cache_timeout)
            
            return queryset
            
        except Exception as e:
            logger.error(f"Erro ao buscar mangás: {str(e)}", exc_info=True)
            raise MangaException("Ocorreu um erro ao buscar os mangás. Por favor, tente novamente mais tarde.")
    
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
        try:
            manga = self.get_manga_by_slug_with_cache(slug)
            if not manga:
                raise MangaNotFoundError(f"Mangá com slug '{slug}' não encontrado.")
            return manga
            
        except MangaNotFoundError:
            raise
            
        except Exception as e:
            logger.error(f"Erro ao buscar mangá por slug '{slug}': {str(e)}", exc_info=True)
            raise MangaException("Ocorreu um erro ao buscar o mangá. Por favor, tente novamente mais tarde.")
    
    @transaction.atomic
    def create_manga(self, manga_data: Dict[str, Any], created_by: User) -> Manga:
        """Cria um novo mangá com validação e cache.
        
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
        try:
            with transaction.atomic():
                # Validar dados obrigatórios
                title = manga_data.get('title', '').strip()
                if not title:
                    raise MangaValidationError({"title": "O título é obrigatório."})
                
                # Verificar se já existe um mangá com o mesmo título
                if Manga.objects.filter(title__iexact=title).exists():
                    raise DuplicateMangaError(f"Já existe um mangá com o título '{title}'.")
                
                # Preparar dados para criação
                manga_data['created_by'] = created_by
                
                # Criar mangá
                manga = Manga.objects.create(
                    title=title,
                    author=manga_data.get('author', ''),
                    description=manga_data.get('description', ''),
                    created_by=created_by,
                    cover_image=manga_data.get('cover_image')
                )
                
                # Invalidar cache
                self._invalidate_manga_cache()
                
                logger.info(f"Mangá criado: {manga.title} (ID: {manga.id})")
                return manga
                
        except (MangaValidationError, DuplicateMangaError):
            raise
        except Exception as e:
            logger.error(f"Erro ao criar mangá: {str(e)}", exc_info=True)
            raise MangaException("Ocorreu um erro ao criar o mangá. Por favor, tente novamente mais tarde.")
    
    @transaction.atomic
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
        try:
            # Obter o mangá existente
            manga = self.get_manga_by_slug(slug)
            
            # Validar dados
            title = manga_data.get('title', manga.title).strip()
            if not title:
                raise MangaValidationError({"title": "O título é obrigatório."})
            
            # Verificar se a atualização resultaria em um título duplicado
            if title.lower() != manga.title.lower() and \
               Manga.objects.filter(title__iexact=title).exists():
                raise DuplicateMangaError(f"Já existe um mangá com o título '{title}'.")
            
            # Atualizar campos
            manga.title = title
            manga.author = manga_data.get('author', manga.author)
            manga.description = manga_data.get('description', manga.description)
            manga.updated_by = updated_by
            
            # Atualizar imagem de capa se fornecida
            if 'cover_image' in manga_data and manga_data['cover_image']:
                manga.cover_image = manga_data['cover_image']
            
            # Salvar alterações
            manga.save()
            
            # Invalidar cache
            self._invalidate_manga_cache(manga.id)
            
            logger.info(f"Mangá atualizado: {manga.title} (ID: {manga.id})")
            return manga
            
        except (MangaNotFoundError, MangaValidationError, DuplicateMangaError):
            raise
        except Exception as e:
            logger.error(f"Erro ao atualizar mangá com slug '{slug}': {str(e)}", exc_info=True)
            raise MangaException("Ocorreu um erro ao atualizar o mangá. Por favor, tente novamente mais tarde.")
    
    @transaction.atomic
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
        try:
            # Verificar se o mangá existe
            manga = self.get_manga_by_slug(slug)
            
            # Marcar como excluído (exclusão lógica)
            manga.is_deleted = True
            manga.deleted_by = deleted_by
            manga.save(update_fields=['is_deleted', 'deleted_by', 'updated_at'])
            
            # Invalidar cache
            self._invalidate_manga_cache(manga.id)
            
            logger.info(f"Mangá removido: {manga.title} (ID: {manga.id})")
            return True
            
        except MangaNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Erro ao remover mangá com slug '{slug}': {str(e)}", exc_info=True)
            raise MangaException("Ocorreu um erro ao remover o mangá. Por favor, tente novamente mais tarde.")
    
    def get_manga_with_cache(self, manga_id: int) -> Optional[Manga]:
        """Obtém mangá por ID com cache."""
        cache_key = f"manga_detail_{manga_id}"
        
        # Tentar buscar no cache
        manga = cache.get(cache_key)
        if manga:
            return manga
        
        # Buscar no banco de dados
        try:
            manga = Manga.objects.select_related().prefetch_related(
                'volumes__capitulos__paginas'
            ).get(id=manga_id, is_published=True, is_deleted=False)
            
            # Armazenar no cache
            cache.set(cache_key, manga, self.cache_timeout)
            return manga
            
        except Manga.DoesNotExist:
            return None
    
    def get_manga_by_slug_with_cache(self, slug: str) -> Optional[Manga]:
        """Obtém mangá por slug com cache."""
        cache_key = f"manga_slug_{slug}"
        
        # Tentar buscar no cache
        manga = cache.get(cache_key)
        if manga:
            return manga
        
        # Buscar no banco de dados
        try:
            manga = Manga.objects.select_related().prefetch_related(
                'volumes__capitulos__paginas'
            ).get(slug=slug, is_deleted=False)
            
            # Armazenar no cache
            cache.set(cache_key, manga, self.cache_timeout)
            return manga
            
        except Manga.DoesNotExist:
            return None
    
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
            MangaException: Se ocorrer um erro ao publicar/despublicar
        """
        try:
            # Obter o mangá
            manga = self.get_manga_by_slug(slug)
            
            # Atualizar status de publicação
            manga.is_published = published
            manga.save(update_fields=['is_published', 'updated_at'])
            
            # Invalidar cache
            self._invalidate_manga_cache(manga.id)
            
            action = "publicado" if published else "despublicado"
            logger.info(f"Mangá {action}: {manga.title} (ID: {manga.id})")
            
            return manga
            
        except MangaNotFoundError:
            raise
        except Exception as e:
            action = "publicar" if published else "despublicar"
            logger.error(f"Erro ao {action} mangá com slug '{slug}': {str(e)}", exc_info=True)
            raise MangaException(f"Não foi possível {action} o mangá. Por favor, tente novamente mais tarde.")
    
    def get_manga_stats(self, manga: Manga) -> Dict[str, Any]:
        """Obtém estatísticas do mangá com cache."""
        cache_key = f"manga_stats_{manga.id}"
        
        # Tentar buscar no cache
        stats = cache.get(cache_key)
        if stats:
            return stats
        
        # Calcular estatísticas
        stats = {
            'total_volumes': manga.volumes.count(),
            'total_chapters': sum(volume.capitulos.count() for volume in manga.volumes.all()),
            'total_pages': sum(
                sum(capitulo.paginas.count() for capitulo in volume.capitulos.all())
                for volume in manga.volumes.all()
            ),
            'view_count': manga.view_count,
            'is_published': manga.is_published,
            'created_at': manga.created_at.isoformat() if manga.created_at else None,
            'updated_at': manga.updated_at.isoformat() if manga.updated_at else None,
        }
        
        # Armazenar no cache
        cache.set(cache_key, stats, self.cache_timeout)
        return stats
    
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
        try:
            from django.db.models import Q
            
            queryset = Manga.objects.filter(is_deleted=False)
            
            # Aplicar busca no título, descrição e títulos alternativos
            if query:
                queryset = queryset.filter(
                    Q(title__icontains=query) | 
                    Q(description__icontains=query) |
                    Q(alternate_titles__icontains=query)
                )
            
            # Aplicar filtros adicionais
            if filters:
                queryset = queryset.filter(**filters)
            
            return queryset.order_by('-created_at')
            
        except Exception as e:
            logger.error(f"Erro ao buscar mangás com query '{query}': {str(e)}", exc_info=True)
            raise MangaException("Ocorreu um erro ao buscar os mangás. Por favor, tente novamente mais tarde.")
    
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
        try:
            # Verificar se o mangá existe
            manga = self.get_manga_by_slug(manga_slug)
            
            # Construir queryset
            queryset = Capitulo.objects.filter(volume__manga=manga)
            
            # Aplicar filtro de publicação
            if published_only:
                queryset = queryset.filter(is_published=True)
            
            # Ordenar por volume e número
            queryset = queryset.order_by('volume__number', 'number')
            
            return queryset
            
        except MangaNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Erro ao buscar capítulos do mangá '{manga_slug}': {str(e)}", exc_info=True)
            raise MangaException("Ocorreu um erro ao buscar os capítulos. Por favor, tente novamente mais tarde.")
    
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
        try:
            # Verificar se o mangá existe
            manga = self.get_manga_by_slug(manga_slug)
            
            # Buscar capítulo
            try:
                chapter = Capitulo.objects.select_related('volume').get(
                    volume__manga=manga,
                    slug=chapter_slug
                )
                return chapter
                
            except Capitulo.DoesNotExist:
                raise ChapterNotFoundError(f"Capítulo com slug '{chapter_slug}' não encontrado.")
                
        except MangaNotFoundError:
            raise
        except ChapterNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Erro ao buscar capítulo '{chapter_slug}' do mangá '{manga_slug}': {str(e)}", exc_info=True)
            raise MangaException("Ocorreu um erro ao buscar o capítulo. Por favor, tente novamente mais tarde.")
    
    @transaction.atomic
    def create_chapter(self, manga_slug: str, chapter_data: Dict[str, Any], created_by: User) -> Capitulo:
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
        try:
            with transaction.atomic():
                # Verificar se o mangá existe
                manga = self.get_manga_by_slug(manga_slug)
                
                # Validar dados obrigatórios
                volume_id = chapter_data.get('volume_id')
                if not volume_id:
                    raise MangaValidationError({"volume_id": "O volume é obrigatório."})
                
                number = chapter_data.get('number')
                if not number:
                    raise MangaValidationError({"number": "O número do capítulo é obrigatório."})
                
                # Verificar se o volume existe e pertence ao mangá
                try:
                    volume = Volume.objects.get(id=volume_id, manga=manga)
                except Volume.DoesNotExist:
                    raise MangaValidationError({"volume_id": "Volume inválido."})
                
                # Verificar se já existe um capítulo com o mesmo número no volume
                if Capitulo.objects.filter(volume=volume, number=number).exists():
                    raise DuplicateChapterError(f"Já existe um capítulo com o número {number} neste volume.")
                
                # Criar capítulo
                chapter = Capitulo.objects.create(
                    volume=volume,
                    number=number,
                    title=chapter_data.get('title', ''),
                    created_by=created_by
                )
                
                # Atualizar contador de capítulos do mangá
                manga.chapter_count = Capitulo.objects.filter(volume__manga=manga).count()
                manga.save(update_fields=['chapter_count', 'updated_at'])
                
                # Invalidar cache
                self._invalidate_manga_cache(manga.id)
                
                logger.info(f"Capítulo criado: {chapter.title or f'Capítulo {chapter.number}'} (ID: {chapter.id})")
                return chapter
                
        except (MangaNotFoundError, MangaValidationError, DuplicateChapterError):
            raise
        except Exception as e:
            logger.error(f"Erro ao criar capítulo para o mangá '{manga_slug}': {str(e)}", exc_info=True)
            raise MangaException("Ocorreu um erro ao criar o capítulo. Por favor, tente novamente mais tarde.")
    
    @transaction.atomic
    def update_chapter(self, manga_slug: str, chapter_slug: str, chapter_data: Dict[str, Any], updated_by: User) -> Capitulo:
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
        try:
            with transaction.atomic():
                # Verificar se o mangá existe
                manga = self.get_manga_by_slug(manga_slug)
                
                # Buscar capítulo
                try:
                    chapter = Capitulo.objects.select_related('volume').get(
                        volume__manga=manga,
                        slug=chapter_slug
                    )
                except Capitulo.DoesNotExist:
                    raise ChapterNotFoundError(f"Capítulo com slug '{chapter_slug}' não encontrado.")
                
                # Verificar se está alterando o volume
                volume_id = chapter_data.get('volume_id')
                if volume_id and volume_id != chapter.volume.id:
                    try:
                        new_volume = Volume.objects.get(id=volume_id, manga=manga)
                        chapter.volume = new_volume
                    except Volume.DoesNotExist:
                        raise MangaValidationError({"volume_id": "Volume inválido."})
                
                # Verificar se está alterando o número do capítulo
                number = chapter_data.get('number')
                if number and number != chapter.number:
                    # Verificar se já existe um capítulo com o mesmo número no volume
                    if Capitulo.objects.filter(volume=chapter.volume, number=number).exists():
                        raise DuplicateChapterError(f"Já existe um capítulo com o número {number} neste volume.")
                    chapter.number = number
                
                # Atualizar outros campos
                if 'title' in chapter_data:
                    chapter.title = chapter_data['title']
                
                chapter.updated_by = updated_by
                chapter.save()
                
                # Invalidar cache
                self._invalidate_manga_cache(manga.id)
                
                logger.info(f"Capítulo atualizado: {chapter.title or f'Capítulo {chapter.number}'} (ID: {chapter.id})")
                return chapter
                
        except (MangaNotFoundError, ChapterNotFoundError, MangaValidationError, DuplicateChapterError):
            raise
        except Exception as e:
            logger.error(f"Erro ao atualizar capítulo '{chapter_slug}' do mangá '{manga_slug}': {str(e)}", exc_info=True)
            raise MangaException("Ocorreu um erro ao atualizar o capítulo. Por favor, tente novamente mais tarde.")
    
    @transaction.atomic
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
        try:
            with transaction.atomic():
                # Verificar se o mangá existe
                manga = self.get_manga_by_slug(manga_slug)
                
                # Buscar capítulo
                try:
                    chapter = Capitulo.objects.select_related('volume').get(
                        volume__manga=manga,
                        slug=chapter_slug
                    )
                except Capitulo.DoesNotExist:
                    raise ChapterNotFoundError(f"Capítulo com slug '{chapter_slug}' não encontrado.")
                
                # Remover capítulo
                chapter_id = chapter.id
                chapter_title = chapter.title or f'Capítulo {chapter.number}'
                chapter.delete()
                
                # Atualizar contador de capítulos do mangá
                manga.chapter_count = Capitulo.objects.filter(volume__manga=manga).count()
                manga.save(update_fields=['chapter_count', 'updated_at'])
                
                # Invalidar cache
                self._invalidate_manga_cache(manga.id)
                
                logger.info(f"Capítulo removido: {chapter_title} (ID: {chapter_id})")
                return True
                
        except (MangaNotFoundError, ChapterNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Erro ao remover capítulo '{chapter_slug}' do mangá '{manga_slug}': {str(e)}", exc_info=True)
            raise MangaException("Ocorreu um erro ao remover o capítulo. Por favor, tente novamente mais tarde.")
    
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
        try:
            # Verificar se o mangá existe
            manga = self.get_manga_by_slug(manga_slug)
            
            # Buscar capítulo
            try:
                chapter = Capitulo.objects.select_related('volume').get(
                    volume__manga=manga,
                    slug=chapter_slug
                )
            except Capitulo.DoesNotExist:
                raise ChapterNotFoundError(f"Capítulo com slug '{chapter_slug}' não encontrado.")
            
            # Atualizar status de publicação
            chapter.is_published = published
            chapter.save(update_fields=['is_published', 'updated_at'])
            
            # Invalidar cache
            self._invalidate_manga_cache(manga.id)
            
            action = "publicado" if published else "despublicado"
            logger.info(f"Capítulo {action}: {chapter.title or f'Capítulo {chapter.number}'} (ID: {chapter.id})")
            
            return chapter
            
        except (MangaNotFoundError, ChapterNotFoundError):
            raise
        except Exception as e:
            action = "publicar" if published else "despublicar"
            logger.error(f"Erro ao {action} capítulo '{chapter_slug}' do mangá '{manga_slug}': {str(e)}", exc_info=True)
            from apps.mangas.exceptions import ChapterPublishingError
            raise ChapterPublishingError(f"Não foi possível {action} o capítulo. Por favor, tente novamente mais tarde.")
    
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
        try:
            # Verificar se o mangá existe
            manga = self.get_manga_by_slug(manga_slug)
            
            # Buscar capítulo
            try:
                chapter = Capitulo.objects.get(
                    volume__manga=manga,
                    slug=chapter_slug
                )
            except Capitulo.DoesNotExist:
                raise ChapterNotFoundError(f"Capítulo com slug '{chapter_slug}' não encontrado.")
            
            # Retornar páginas ordenadas por número
            return Pagina.objects.filter(capitulo=chapter).order_by('number')
            
        except (MangaNotFoundError, ChapterNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Erro ao buscar páginas do capítulo '{chapter_slug}' do mangá '{manga_slug}': {str(e)}", exc_info=True)
            raise MangaException("Ocorreu um erro ao buscar as páginas. Por favor, tente novamente mais tarde.")
    
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
        try:
            # Verificar se o mangá existe
            manga = self.get_manga_by_slug(manga_slug)
            
            # Buscar capítulo
            try:
                chapter = Capitulo.objects.get(
                    volume__manga=manga,
                    slug=chapter_slug
                )
            except Capitulo.DoesNotExist:
                raise ChapterNotFoundError(f"Capítulo com slug '{chapter_slug}' não encontrado.")
            
            # Buscar página
            try:
                page = Pagina.objects.get(capitulo=chapter, number=page_number)
                return page
            except Pagina.DoesNotExist:
                raise PageNotFoundError(f"Página {page_number} não encontrada.")
                
        except (MangaNotFoundError, ChapterNotFoundError, PageNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Erro ao buscar página {page_number} do capítulo '{chapter_slug}' do mangá '{manga_slug}': {str(e)}", exc_info=True)
            raise MangaException("Ocorreu um erro ao buscar a página. Por favor, tente novamente mais tarde.")
    
    @transaction.atomic
    def add_page(self, manga_slug: str, chapter_slug: str, image_file: UploadedFile, created_by: User, page_number: Optional[int] = None) -> Pagina:
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
        try:
            with transaction.atomic():
                # Verificar se o mangá existe
                manga = self.get_manga_by_slug(manga_slug)
                
                # Buscar capítulo
                try:
                    chapter = Capitulo.objects.get(
                        volume__manga=manga,
                        slug=chapter_slug
                    )
                except Capitulo.DoesNotExist:
                    raise ChapterNotFoundError(f"Capítulo com slug '{chapter_slug}' não encontrado.")
                
                # Validar arquivo de imagem
                self._validate_image_file(image_file)
                
                # Determinar número da página
                if page_number is None:
                    # Obter o próximo número disponível
                    max_number = Pagina.objects.filter(capitulo=chapter).aggregate(Max('number'))['number__max'] or 0
                    page_number = max_number + 1
                else:
                    # Verificar se já existe uma página com o mesmo número
                    if Pagina.objects.filter(capitulo=chapter, number=page_number).exists():
                        raise DuplicatePageError(f"Já existe uma página com o número {page_number} neste capítulo.")
                
                # Verificar limite de páginas por capítulo
                if Pagina.objects.filter(capitulo=chapter).count() >= MAX_PAGES_PER_CHAPTER:
                    raise MangaValidationError({"page": f"O capítulo já atingiu o limite máximo de {MAX_PAGES_PER_CHAPTER} páginas."})
                
                # Criar página
                page = Pagina.objects.create(
                    capitulo=chapter,
                    number=page_number,
                    image=image_file,
                    created_by=created_by
                )
                
                # Invalidar cache
                self._invalidate_manga_cache(manga.id)
                
                logger.info(f"Página adicionada: Página {page.number} do capítulo '{chapter.title or f'Capítulo {chapter.number}'}' (ID: {page.id})")
                return page
                
        except (MangaNotFoundError, ChapterNotFoundError, InvalidFileError, FileTooLargeError, 
                UnsupportedFileTypeError, DuplicatePageError, MangaValidationError):
            raise
        except Exception as e:
            logger.error(f"Erro ao adicionar página ao capítulo '{chapter_slug}' do mangá '{manga_slug}': {str(e)}", exc_info=True)
            from apps.mangas.exceptions import PageProcessingError
            raise PageProcessingError("Ocorreu um erro ao processar a imagem. Por favor, tente novamente mais tarde.")
    
    @transaction.atomic
    def update_page(self, manga_slug: str, chapter_slug: str, page_number: int, image_file: UploadedFile, updated_by: User) -> Pagina:
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
        try:
            with transaction.atomic():
                # Verificar se o mangá existe
                manga = self.get_manga_by_slug(manga_slug)
                
                # Buscar capítulo
                try:
                    chapter = Capitulo.objects.get(
                        volume__manga=manga,
                        slug=chapter_slug
                    )
                except Capitulo.DoesNotExist:
                    raise ChapterNotFoundError(f"Capítulo com slug '{chapter_slug}' não encontrado.")
                
                # Buscar página
                try:
                    page = Pagina.objects.get(capitulo=chapter, number=page_number)
                except Pagina.DoesNotExist:
                    raise PageNotFoundError(f"Página {page_number} não encontrada.")
                
                # Validar arquivo de imagem
                self._validate_image_file(image_file)
                
                # Atualizar imagem
                page.image = image_file
                page.updated_by = updated_by
                page.save()
                
                # Invalidar cache
                self._invalidate_manga_cache(manga.id)
                
                logger.info(f"Página atualizada: Página {page.number} do capítulo '{chapter.title or f'Capítulo {chapter.number}'}' (ID: {page.id})")
                return page
                
        except (MangaNotFoundError, ChapterNotFoundError, PageNotFoundError, 
                InvalidFileError, FileTooLargeError, UnsupportedFileTypeError):
            raise
        except Exception as e:
            logger.error(f"Erro ao atualizar página {page_number} do capítulo '{chapter_slug}' do mangá '{manga_slug}': {str(e)}", exc_info=True)
            from apps.mangas.exceptions import PageProcessingError
            raise PageProcessingError("Ocorreu um erro ao processar a imagem. Por favor, tente novamente mais tarde.")
    
    @transaction.atomic
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
        try:
            with transaction.atomic():
                # Verificar se o mangá existe
                manga = self.get_manga_by_slug(manga_slug)
                
                # Buscar capítulo
                try:
                    chapter = Capitulo.objects.get(
                        volume__manga=manga,
                        slug=chapter_slug
                    )
                except Capitulo.DoesNotExist:
                    raise ChapterNotFoundError(f"Capítulo com slug '{chapter_slug}' não encontrado.")
                
                # Buscar página
                try:
                    page = Pagina.objects.get(capitulo=chapter, number=page_number)
                except Pagina.DoesNotExist:
                    raise PageNotFoundError(f"Página {page_number} não encontrada.")
                
                # Remover página
                page_id = page.id
                page.delete()
                
                # Invalidar cache
                self._invalidate_manga_cache(manga.id)
                
                logger.info(f"Página removida: Página {page_number} do capítulo '{chapter.title or f'Capítulo {chapter.number}'}' (ID: {page_id})")
                return True
                
        except (MangaNotFoundError, ChapterNotFoundError, PageNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Erro ao remover página {page_number} do capítulo '{chapter_slug}' do mangá '{manga_slug}': {str(e)}", exc_info=True)
            raise MangaException("Ocorreu um erro ao remover a página. Por favor, tente novamente mais tarde.")
    
    @transaction.atomic
    def reorder_pages(self, manga_slug: str, chapter_slug: str, new_order: Dict[int, int], updated_by: User) -> bool:
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
        try:
            with transaction.atomic():
                # Verificar se o mangá existe
                manga = self.get_manga_by_slug(manga_slug)
                
                # Buscar capítulo
                try:
                    chapter = Capitulo.objects.get(
                        volume__manga=manga,
                        slug=chapter_slug
                    )
                except Capitulo.DoesNotExist:
                    raise ChapterNotFoundError(f"Capítulo com slug '{chapter_slug}' não encontrado.")
                
                # Validar nova ordem
                existing_pages = list(Pagina.objects.filter(capitulo=chapter).values_list('number', flat=True))
                if set(new_order.keys()) != set(existing_pages):
                    raise MangaValidationError({"new_order": "A nova ordem deve incluir todas as páginas existentes."})
                
                if set(new_order.values()) != set(existing_pages):
                    raise MangaValidationError({"new_order": "A nova ordem deve conter os mesmos números de página que existem atualmente."})
                
                # Aplicar nova ordem
                for old_number, new_number in new_order.items():
                    if old_number != new_number:
                        page = Pagina.objects.get(capitulo=chapter, number=old_number)
                        
                        # Usar um número temporário para evitar conflitos de unicidade
                        temp_number = -old_number
                        page.number = temp_number
                        page.save(update_fields=['number'])
                
                # Aplicar os números finais
                for old_number, new_number in new_order.items():
                    if old_number != new_number:
                        page = Pagina.objects.get(capitulo=chapter, number=-old_number)
                        page.number = new_number
                        page.updated_by = updated_by
                        page.save()
                
                # Invalidar cache
                self._invalidate_manga_cache(manga.id)
                
                logger.info(f"Páginas reordenadas no capítulo '{chapter.title or f'Capítulo {chapter.number}'}' do mangá '{manga.title}'")
                return True
                
        except (MangaNotFoundError, ChapterNotFoundError, MangaValidationError):
            raise
        except Exception as e:
            logger.error(f"Erro ao reordenar páginas do capítulo '{chapter_slug}' do mangá '{manga_slug}': {str(e)}", exc_info=True)
            raise MangaException("Ocorreu um erro ao reordenar as páginas. Por favor, tente novamente mais tarde.")
    
    def _validate_image_file(self, image_file: UploadedFile) -> None:
        """Valida um arquivo de imagem."""
        # Verificar se o arquivo é uma imagem válida
        validator = ImageFileValidator()
        try:
            validator(image_file)
        except ValidationError as e:
            from apps.mangas.exceptions import InvalidFileError
            raise InvalidFileError(str(e))
    
    def _invalidate_manga_cache(self, manga_id: Optional[int] = None):
        """Invalida cache relacionado a mangás."""
        if manga_id:
            # Invalidar cache específico do mangá
            cache.delete(f"manga_detail_{manga_id}")
            cache.delete(f"manga_stats_{manga_id}")
            
            # Buscar slug para invalidar cache por slug
            try:
                manga = Manga.objects.get(id=manga_id)
                cache.delete(f"manga_slug_{manga.slug}")
            except Manga.DoesNotExist:
                pass
        
        # Invalidar cache geral
        cache.delete('manga_list')
        cache.delete('latest_manga_updates')
        cache.delete('manga_stats')

# Instância global do serviço
unified_manga_service = UnifiedMangaService()