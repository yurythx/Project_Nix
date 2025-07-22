from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from django.db.models import QuerySet
from django.contrib.auth import get_user_model

User = get_user_model()

class IPageService(ABC):
    """Interface para serviços de páginas"""
    
    @abstractmethod
    def get_homepage(self):
        """
        Obtém a página inicial
        :return: Página inicial ou None
        """
        pass
    
    @abstractmethod
    def get_page_by_slug(self, slug: str):
        """
        Obtém página por slug
        :param slug: Slug da página
        :return: Página encontrada
        """
        pass
    
    @abstractmethod
    def get_published_pages(self) -> QuerySet:
        """
        Obtém todas as páginas publicadas
        :return: QuerySet de páginas publicadas
        """
        pass
    
    @abstractmethod
    def get_menu_pages(self) -> QuerySet:
        """
        Obtém páginas para exibir no menu
        :return: QuerySet de páginas do menu
        """
        pass
    
    @abstractmethod
    def create_page(self, page_data: Dict[str, Any], created_by: User):
        """
        Cria uma nova página
        :param page_data: Dados da página
        :param created_by: Usuário que está criando
        :return: Página criada
        """
        pass
    
    @abstractmethod
    def update_page(self, page_id: int, page_data: Dict[str, Any], updated_by: User):
        """
        Atualiza uma página
        :param page_id: ID da página
        :param page_data: Dados para atualização
        :param updated_by: Usuário que está atualizando
        :return: Página atualizada
        """
        pass
    
    @abstractmethod
    def delete_page(self, page_id: int, deleted_by: User) -> bool:
        """
        Deleta uma página
        :param page_id: ID da página
        :param deleted_by: Usuário que está deletando
        :return: True se deletado com sucesso
        """
        pass
    
    @abstractmethod
    def increment_page_views(self, page_id: int) -> None:
        """
        Incrementa contador de visualizações
        :param page_id: ID da página
        """
        pass
    
    @abstractmethod
    def search_pages(self, query: str) -> QuerySet:
        """
        Busca páginas por termo
        :param query: Termo de busca
        :return: QuerySet de páginas encontradas
        """
        pass

class INavigationService(ABC):
    """Interface para serviços de navegação"""
    
    @abstractmethod
    def get_main_navigation(self) -> List[Dict]:
        """
        Obtém navegação principal
        :return: Lista de itens de navegação
        """
        pass
    
    @abstractmethod
    def get_breadcrumbs(self, page) -> List[Dict]:
        """
        Obtém breadcrumbs para uma página
        :param page: Página atual
        :return: Lista de breadcrumbs
        """
        pass
    
    @abstractmethod
    def create_navigation_item(self, item_data: Dict[str, Any]):
        """
        Cria item de navegação
        :param item_data: Dados do item
        :return: Item criado
        """
        pass
    
    @abstractmethod
    def update_navigation_order(self, items_order: List[Dict]) -> bool:
        """
        Atualiza ordem dos itens de navegação
        :param items_order: Lista com IDs e novas ordens
        :return: True se atualizado com sucesso
        """
        pass

class ISEOService(ABC):
    """Interface para serviços de SEO"""
    
    @abstractmethod
    def get_seo_settings(self):
        """
        Obtém configurações de SEO
        :return: Configurações de SEO
        """
        pass
    
    @abstractmethod
    def update_seo_settings(self, seo_data: Dict[str, Any]):
        """
        Atualiza configurações de SEO
        :param seo_data: Dados de SEO
        :return: Configurações atualizadas
        """
        pass
    
    @abstractmethod
    def generate_meta_tags(self, page) -> Dict[str, str]:
        """
        Gera meta tags para uma página
        :param page: Página
        :return: Dicionário com meta tags
        """
        pass
    
    @abstractmethod
    def generate_structured_data(self, page) -> Dict[str, Any]:
        """
        Gera dados estruturados (Schema.org) para uma página
        :param page: Página
        :return: Dados estruturados
        """
        pass
    
    @abstractmethod
    def generate_sitemap_data(self) -> List[Dict]:
        """
        Gera dados para sitemap
        :return: Lista de URLs para sitemap
        """
        pass

class IAnalyticsService(ABC):
    """Interface para serviços de analytics"""
    
    @abstractmethod
    def track_page_view(self, page, request) -> None:
        """
        Registra visualização de página
        :param page: Página visualizada
        :param request: Request HTTP
        """
        pass
    
    @abstractmethod
    def get_page_analytics(self, page_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Obtém analytics de uma página
        :param page_id: ID da página
        :param days: Número de dias para análise
        :return: Dados de analytics
        """
        pass
    
    @abstractmethod
    def get_popular_pages(self, limit: int = 10) -> QuerySet:
        """
        Obtém páginas mais populares
        :param limit: Limite de resultados
        :return: QuerySet de páginas populares
        """
        pass
