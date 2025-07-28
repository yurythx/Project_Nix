"""
Implementação do serviço de gerenciamento de mangás.

Este módulo contém a implementação concreta do serviço de mangás,
seguindo a interface IMangaService e aplicando os princípios SOLID.
"""

import logging
from typing import Dict, Any, Optional, List

from django.db import transaction
from django.db.models import QuerySet, Q
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import UploadedFile
from django.utils.text import slugify

from ..interfaces.services import IMangaService
from ..interfaces.manga_repository_interface import MangaRepositoryInterface
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
from ..constants import (
    MAX_IMAGE_SIZE, MAX_IMAGE_WIDTH, MAX_IMAGE_HEIGHT,
    ALLOWED_IMAGE_TYPES, MAX_CHAPTER_NUMBER, MAX_PAGES_PER_CHAPTER
)

# Configuração de logging
logger = logging.getLogger(__name__)
User = get_user_model()

class MangaService(IMangaService):
    """
    Implementação do serviço de gerenciamento de mangás.
    
    Esta classe implementa a interface IMangaService, fornecendo operações
    completas de CRUD para mangás, capítulos e páginas, além de validações
    de negócio e tratamento de erros.
    
    Princípios SOLID aplicados:
    - Single Responsibility: Cada método tem uma única responsabilidade
    - Open/Closed: Aberto para extensão, fechado para modificação
    - Liskov Substitution: Pode ser substituído por qualquer implementação de IMangaService
    - Interface Segregation: Depende apenas da interface que precisa
    - Dependency Inversion: Depende de abstrações (interfaces), não de implementações concretas
    """
    
    def __init__(self, repository: MangaRepositoryInterface = None):
        """
        Inicializa o serviço com injeção de dependência.
        
        Args:
            repository: Implementação do repositório para acesso a dados
        """
        self.repository = repository or MangaRepositoryInterface()
    
    # Implementação dos métodos da interface IMangaService
    
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
            queryset = self.repository.list_mangas()
            
            # Aplica filtros de publicação
            if published_only:
                queryset = queryset.filter(is_published=True)
            
            # Aplica filtros adicionais
            if filters:
                queryset = queryset.filter(**filters)
            
            return queryset.order_by('-created_at')
            
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
            manga = self.repository.get_manga_by_slug(slug)
            if not manga:
                raise MangaNotFoundError(f"Mangá com slug '{slug}' não encontrado.")
            return manga
            
        except MangaNotFoundError:
            raise
            
        except Exception as e:
            logger.error(f"Erro ao buscar mangá por slug '{slug}': {str(e)}", exc_info=True)
            raise MangaException("Ocorreu um erro ao buscar o mangá. Por favor, tente novamente mais tarde.")
    
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
            queryset = self.repository.list_mangas()
            
            # Aplica busca no título e descrição
            if query:
                queryset = queryset.filter(
                    Q(title__icontains=query) | 
                    Q(description__icontains=query) |
                    Q(alternate_titles__icontains=query)
                )
            
            # Aplica filtros adicionais
            if filters:
                queryset = queryset.filter(**filters)
            
            return queryset.order_by('-created_at')
            
        except Exception as e:
            logger.error(f"Erro ao buscar mangás com query '{query}': {str(e)}", exc_info=True)
            raise MangaException("Ocorreu um erro ao buscar os mangás. Por favor, tente novamente mais tarde.")
    
    @transaction.atomic
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
        try:
            # Validação dos dados
            title = manga_data.get('title', '').strip()
            if not title:
                raise MangaValidationError({"title": "O título é obrigatório."})
            
            # Verifica se já existe um mangá com o mesmo título
            if self.repository.list_mangas().filter(title__iexact=title).exists():
                raise DuplicateMangaError(f"Já existe um mangá com o título '{title}'.")
            
            # Prepara os dados para criação
            manga_data['created_by'] = created_by
            manga_data['slug'] = slugify(title)
            
            # Cria o mangá
            manga = self.repository.create_manga(manga_data)
            logger.info(f"Mangá criado com sucesso: {manga.title} (ID: {manga.id})")
            
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
            # Obtém o mangá existente
            manga = self.get_manga_by_slug(slug)
            
            # Validação dos dados
            title = manga_data.get('title', manga.title).strip()
            if not title:
                raise MangaValidationError({"title": "O título é obrigatório."})
            
            # Verifica se a atualização resultaria em um título duplicado
            if title.lower() != manga.title.lower() and \
               self.repository.list_mangas().filter(title__iexact=title).exists():
                raise DuplicateMangaError(f"Já existe um mangá com o título '{title}'.")
            
            # Prepara os dados para atualização
            manga_data['updated_by'] = updated_by
            if 'title' in manga_data and manga_data['title'] != manga.title:
                manga_data['slug'] = slugify(manga_data['title'])
            
            # Atualiza o mangá
            updated_manga = self.repository.update_manga(manga.slug, manga_data)
            logger.info(f"Mangá atualizado com sucesso: {updated_manga.title} (ID: {updated_manga.id})")
            
            return updated_manga
            
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
            # Verifica se o mangá existe
            manga = self.get_manga_by_slug(slug)
            
            # Marca como excluído (exclusão lógica)
            manga.is_deleted = True
            manga.deleted_by = deleted_by
            manga.save(update_fields=['is_deleted', 'deleted_by', 'updated_at'])
            
            logger.info(f"Mangá removido com sucesso: {manga.title} (ID: {manga.id})")
            return True
            
        except MangaNotFoundError:
            raise
            
        except Exception as e:
            logger.error(f"Erro ao remover mangá com slug '{slug}': {str(e)}", exc_info=True)
            raise MangaException("Ocorreu um erro ao remover o mangá. Por favor, tente novamente mais tarde.")
    
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
        try:
            manga = self.get_manga_by_slug(slug)
            
            # Atualiza o status de publicação
            manga.is_published = published
            manga.save(update_fields=['is_published', 'updated_at'])
            
            action = "publicado" if published else "despublicado"
            logger.info(f"Mangá {action} com sucesso: {manga.title} (ID: {manga.id})")
            
            return manga
            
        except MangaNotFoundError:
            raise
            
        except Exception as e:
            action = "publicar" if published else "despublicar"
            logger.error(f"Erro ao {action} mangá com slug '{slug}': {str(e)}", exc_info=True)
            raise MangaPublishingError(
                f"Não foi possível {action} o mangá. Por favor, tente novamente mais tarde."
            )
    
    # Métodos para gerenciamento de capítulos
    
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
            manga = self.get_manga_by_slug(manga_slug)
            queryset = self.repository.list_capitulos(manga)
            
            # Filtra por status de publicação, se necessário
            if published_only:
                queryset = queryset.filter(is_published=True)
            
            return queryset.order_by('number')
            
        except MangaNotFoundError:
            raise
            
        except Exception as e:
            logger.error(
                f"Erro ao buscar capítulos do mangá com slug '{manga_slug}': {str(e)}", 
                exc_info=True
            )
            raise MangaException(
                "Ocorreu um erro ao buscar os capítulos do mangá. Por favor, tente novamente mais tarde."
            )
    
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
            manga = self.get_manga_by_slug(manga_slug)
            chapter = self.repository.get_capitulo_by_slug(manga, chapter_slug)
            
            if not chapter:
                raise ChapterNotFoundError(
                    f"Capítulo com slug '{chapter_slug}' não encontrado no mangá '{manga.title}'."
                )
                
            return chapter
            
        except (MangaNotFoundError, ChapterNotFoundError):
            raise
            
        except Exception as e:
            logger.error(
                f"Erro ao buscar capítulo com slug '{chapter_slug}' do mangá '{manga_slug}': {str(e)}", 
                exc_info=True
            )
            raise MangaException(
                "Ocorreu um erro ao buscar o capítulo. Por favor, tente novamente mais tarde."
            )
    
    @transaction.atomic
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
        try:
            # Obtém o mangá
            manga = self.get_manga_by_slug(manga_slug)
            
            # Validação dos dados
            number = chapter_data.get('number')
            if number is None:
                raise MangaValidationError({"number": "O número do capítulo é obrigatório."})
            
            if not isinstance(number, (int, float)) or number <= 0:
                raise MangaValidationError({"number": "O número do capítulo deve ser um valor positivo."})
            
            if number > MAX_CHAPTER_NUMBER:
                raise MangaValidationError({
                    "number": f"O número do capítulo não pode ser maior que {MAX_CHAPTER_NUMBER}."
                })
            
            # Verifica se já existe um capítulo com o mesmo número
            if self.repository.list_capitulos(manga).filter(number=number).exists():
                raise DuplicateChapterError(
                    f"Já existe um capítulo com o número {number} neste mangá."
                )
            
            # Prepara os dados para criação
            chapter_data['manga'] = manga
            chapter_data['created_by'] = created_by
            
            # Define o slug baseado no número do capítulo
            if 'title' not in chapter_data or not chapter_data['title'].strip():
                chapter_data['title'] = f"Capítulo {number}"
            
            if 'slug' not in chapter_data or not chapter_data['slug'].strip():
                chapter_data['slug'] = f"capitulo-{number}"
            
            # Cria o capítulo
            chapter = self.repository.create_capitulo(manga, chapter_data)
            
            # Atualiza a contagem de capítulos do mangá
            manga.chapter_count = self.repository.list_capitulos(manga).count()
            manga.save(update_fields=['chapter_count', 'updated_at'])
            
            logger.info(
                f"Capítulo {chapter.number} criado com sucesso para o mangá {manga.title} "
                f"(Manga ID: {manga.id}, Capítulo ID: {chapter.id})"
            )
            
            return chapter
            
        except (MangaNotFoundError, MangaValidationError, DuplicateChapterError):
            raise
            
        except Exception as e:
            logger.error(
                f"Erro ao criar capítulo para o mangá com slug '{manga_slug}': {str(e)}", 
                exc_info=True
            )
            raise MangaException(
                "Ocorreu um erro ao criar o capítulo. Por favor, tente novamente mais tarde."
            )
    
    @transaction.atomic
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
        try:
            # Obtém o capítulo existente
            chapter = self.get_chapter_by_slug(manga_slug, chapter_slug)
            
            # Validação dos dados
            number = chapter_data.get('number', chapter.number)
            if number != chapter.number:  # Se o número está sendo alterado
                if not isinstance(number, (int, float)) or number <= 0:
                    raise MangaValidationError({
                        "number": "O número do capítulo deve ser um valor positivo."
                    })
                
                if number > MAX_CHAPTER_NUMBER:
                    raise MangaValidationError({
                        "number": f"O número do capítulo não pode ser maior que {MAX_CHAPTER_NUMBER}."
                    })
                
                # Verifica se já existe outro capítulo com o novo número
                if self.repository.list_capitulos(chapter.manga).filter(number=number).exists():
                    raise DuplicateChapterError(
                        f"Já existe um capítulo com o número {number} neste mangá."
                    )
            
            # Prepara os dados para atualização
            chapter_data['updated_by'] = updated_by
            
            # Atualiza o capítulo
            updated_chapter = self.repository.update_capitulo(
                chapter.manga, chapter_slug, chapter_data
            )
            
            logger.info(
                f"Capítulo {updated_chapter.number} atualizado com sucesso para o mangá "
                f"{updated_chapter.manga.title} (Manga ID: {updated_chapter.manga.id}, "
                f"Capítulo ID: {updated_chapter.id})"
            )
            
            return updated_chapter
            
        except (MangaNotFoundError, ChapterNotFoundError, MangaValidationError, DuplicateChapterError):
            raise
            
        except Exception as e:
            logger.error(
                f"Erro ao atualizar capítulo com slug '{chapter_slug}' do mangá '{manga_slug}': {str(e)}", 
                exc_info=True
            )
            raise MangaException(
                "Ocorreu um erro ao atualizar o capítulo. Por favor, tente novamente mais tarde."
            )
    
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
            # Obtém o capítulo
            chapter = self.get_chapter_by_slug(manga_slug, chapter_slug)
            manga = chapter.manga
            
            # Remove o capítulo
            self.repository.delete_capitulo(manga, chapter_slug)
            
            # Atualiza a contagem de capítulos do mangá
            manga.chapter_count = self.repository.list_capitulos(manga).count()
            manga.save(update_fields=['chapter_count', 'updated_at'])
            
            logger.info(
                f"Capítulo {chapter.number} removido com sucesso do mangá {manga.title} "
                f"(Manga ID: {manga.id}, Capítulo ID: {chapter.id})"
            )
            
            return True
            
        except (MangaNotFoundError, ChapterNotFoundError):
            raise
            
        except Exception as e:
            logger.error(
                f"Erro ao remover capítulo com slug '{chapter_slug}' do mangá '{manga_slug}': {str(e)}", 
                exc_info=True
            )
            raise MangaException(
                "Ocorreu um erro ao remover o capítulo. Por favor, tente novamente mais tarde."
            )
    
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
            # Obtém o capítulo
            chapter = self.get_chapter_by_slug(manga_slug, chapter_slug)
            
            # Atualiza o status de publicação
            chapter.is_published = published
            chapter.save(update_fields=['is_published', 'updated_at'])
            
            action = "publicado" if published else "despublicado"
            logger.info(
                f"Capítulo {chapter.number} {action} com sucesso para o mangá {chapter.manga.title} "
                f"(Manga ID: {chapter.manga.id}, Capítulo ID: {chapter.id})"
            )
            
            return chapter
            
        except (MangaNotFoundError, ChapterNotFoundError):
            raise
            
        except Exception as e:
            action = "publicar" if published else "despublicar"
            logger.error(
                f"Erro ao {action} capítulo com slug '{chapter_slug}' do mangá '{manga_slug}': {str(e)}", 
                exc_info=True
            )
            raise ChapterPublishingError(
                f"Não foi possível {action} o capítulo. Por favor, tente novamente mais tarde."
            )
    
    # Implementação dos métodos para gerenciamento de páginas
    # ... (os métodos para gerenciamento de páginas serão implementados na próxima iteração)
    
    # Métodos auxiliares
    
    def _validate_image_file(self, image_file: UploadedFile) -> None:
        """
        Valida um arquivo de imagem.
        
        Args:
            image_file: Arquivo de imagem a ser validado
            
        Raises:
            InvalidFileError: Se o arquivo for inválido
            FileTooLargeError: Se o arquivo for muito grande
            UnsupportedFileTypeError: Se o tipo de arquivo não for suportado
        """
        if not image_file or not hasattr(image_file, 'content_type'):
            raise InvalidFileError("Arquivo de imagem inválido.")
        
        # Verifica o tipo do arquivo
        content_type = image_file.content_type.lower()
        if not any(content_type.startswith(f"image/{ext}") for ext in ALLOWED_IMAGE_TYPES):
            raise UnsupportedFileTypeError(
                f"Tipo de arquivo não suportado. Tipos permitidos: {', '.join(ALLOWED_IMAGE_TYPES)}"
            )
        
        # Verifica o tamanho do arquivo
        if image_file.size > MAX_IMAGE_SIZE:
            raise FileTooLargeError(
                f"O arquivo é muito grande. Tamanho máximo permitido: {MAX_IMAGE_SIZE/1024/1024:.1f}MB"
            )