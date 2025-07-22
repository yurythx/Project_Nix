from typing import Dict, Any
from django.db.models import QuerySet
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.pages.interfaces.services import IPageService
from apps.pages.interfaces.repositories import IPageRepository
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class PageService(IPageService):
    """Serviço para gerenciamento de páginas"""
    
    def __init__(self, page_repository: IPageRepository):
        self.page_repository = page_repository
    
    def get_homepage(self):
        """
        Obtém a página inicial
        :return: Página inicial ou None
        """
        try:
            return self.page_repository.get_homepage()
        except Exception as e:
            logger.error(f"Erro ao obter homepage: {str(e)}")
            return None
    
    def get_page_by_slug(self, slug: str):
        """
        Obtém página por slug
        :param slug: Slug da página
        :return: Página encontrada
        """
        return self.page_repository.get_by_slug(slug)
    
    def get_published_pages(self) -> QuerySet:
        """
        Obtém todas as páginas publicadas
        :return: QuerySet de páginas publicadas
        """
        return self.page_repository.list_published()
    
    def get_menu_pages(self) -> QuerySet:
        """
        Obtém páginas para exibir no menu
        :return: QuerySet de páginas do menu
        """
        return self.page_repository.list_menu_pages()
    
    @transaction.atomic
    def create_page(self, page_data: Dict[str, Any], created_by: User):
        """
        Cria uma nova página
        :param page_data: Dados da página
        :param created_by: Usuário que está criando
        :return: Página criada
        """
        # Validações
        title = page_data.get('title')
        if not title:
            raise ValueError("Título é obrigatório")
        
        slug = page_data.get('slug')
        if slug and self.page_repository.exists_by_slug(slug):
            raise ValueError(f"Já existe uma página com o slug '{slug}'")
        
        # Adiciona dados de auditoria
        page_data['created_by'] = created_by
        page_data['updated_by'] = created_by
        
        # Se for definida como homepage, remove homepage atual
        if page_data.get('is_homepage'):
            self._clear_current_homepage()
        
        # Cria a página
        page = self.page_repository.create(page_data)
        
        logger.info(f"Página criada: {page.title} por {created_by.email}")
        return page
    
    @transaction.atomic
    def update_page(self, page_id: int, page_data: Dict[str, Any], updated_by: User):
        """
        Atualiza uma página
        :param page_id: ID da página
        :param page_data: Dados para atualização
        :param updated_by: Usuário que está atualizando
        :return: Página atualizada
        """
        # Obtém a página
        page = self.page_repository.get_by_id(page_id)
        
        # Validações
        slug = page_data.get('slug')
        if slug and slug != page.slug:
            if self.page_repository.exists_by_slug(slug, exclude_id=page_id):
                raise ValueError(f"Já existe uma página com o slug '{slug}'")
        
        # Se for definida como homepage, remove homepage atual
        if page_data.get('is_homepage') and not page.is_homepage:
            self._clear_current_homepage()
        
        # Adiciona dados de auditoria
        page_data['updated_by'] = updated_by
        
        # Atualiza a página
        updated_page = self.page_repository.update(page_id, page_data)
        
        logger.info(f"Página atualizada: {updated_page.title} por {updated_by.email}")
        return updated_page
    
    @transaction.atomic
    def delete_page(self, page_id: int, deleted_by: User) -> bool:
        """
        Deleta uma página
        :param page_id: ID da página
        :param deleted_by: Usuário que está deletando
        :return: True se deletado com sucesso
        """
        try:
            # Obtém a página antes de deletar
            page = self.page_repository.get_by_id(page_id)
            
            # Validações
            if page.is_homepage:
                raise ValueError("Não é possível deletar a página inicial")
            
            # Verifica se tem páginas filhas
            children = self.page_repository.get_children(page_id)
            if children.exists():
                raise ValueError("Não é possível deletar página que possui páginas filhas")
            
            # Deleta a página
            success = self.page_repository.delete(page_id)
            
            if success:
                logger.info(f"Página deletada: {page.title} por {deleted_by.email}")
            
            return success
        except Exception as e:
            logger.error(f"Erro ao deletar página {page_id}: {str(e)}")
            raise
    
    def increment_page_views(self, page_id: int) -> None:
        """
        Incrementa contador de visualizações
        :param page_id: ID da página
        """
        self.page_repository.increment_view_count(page_id)
    
    def search_pages(self, query: str) -> QuerySet:
        """
        Busca páginas por termo
        :param query: Termo de busca
        :return: QuerySet de páginas encontradas
        """
        return self.page_repository.search(query)
    
    def get_popular_pages(self, limit: int = 10) -> QuerySet:
        """
        Obtém páginas mais populares
        :param limit: Limite de resultados
        :return: QuerySet de páginas populares
        """
        return self.page_repository.get_popular_pages(limit)
    
    def publish_page(self, page_id: int, published_by: User):
        """
        Publica uma página
        :param page_id: ID da página
        :param published_by: Usuário que está publicando
        :return: Página publicada
        """
        page = self.page_repository.publish_page(page_id)
        logger.info(f"Página publicada: {page.title} por {published_by.email}")
        return page
    
    def unpublish_page(self, page_id: int, unpublished_by: User):
        """
        Despublica uma página
        :param page_id: ID da página
        :param unpublished_by: Usuário que está despublicando
        :return: Página despublicada
        """
        page = self.page_repository.unpublish_page(page_id)
        logger.info(f"Página despublicada: {page.title} por {unpublished_by.email}")
        return page
    
    def get_breadcrumbs(self, page):
        """
        Obtém breadcrumbs para uma página
        :param page: Página atual
        :return: Lista de breadcrumbs
        """
        return self.page_repository.get_breadcrumb_pages(page)
    
    def _clear_current_homepage(self):
        """Remove homepage atual"""
        try:
            current_homepage = self.page_repository.get_homepage()
            if current_homepage:
                self.page_repository.update(current_homepage.id, {'is_homepage': False})
        except Exception:
            # Se não há homepage atual, continua
            pass
