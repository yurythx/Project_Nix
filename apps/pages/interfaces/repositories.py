from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from django.db.models import QuerySet

class IPageRepository(ABC):
    """Interface para repositório de páginas"""
    
    @abstractmethod
    def create(self, page_data: Dict[str, Any]):
        """Cria uma nova página"""
        pass
    
    @abstractmethod
    def get_by_id(self, page_id: int):
        """Obtém página por ID"""
        pass
    
    @abstractmethod
    def get_by_slug(self, slug: str):
        """Obtém página por slug"""
        pass
    
    @abstractmethod
    def get_homepage(self):
        """Obtém página inicial"""
        pass
    
    @abstractmethod
    def update(self, page_id: int, page_data: Dict[str, Any]):
        """Atualiza página"""
        pass
    
    @abstractmethod
    def delete(self, page_id: int) -> bool:
        """Deleta página"""
        pass
    
    @abstractmethod
    def list_published(self) -> QuerySet:
        """Lista páginas publicadas"""
        pass
    
    @abstractmethod
    def list_menu_pages(self) -> QuerySet:
        """Lista páginas para menu"""
        pass
    
    @abstractmethod
    def search(self, query: str) -> QuerySet:
        """Busca páginas por termo"""
        pass
    
    @abstractmethod
    def get_popular_pages(self, limit: int = 10) -> QuerySet:
        """Obtém páginas mais populares"""
        pass
    
    @abstractmethod
    def increment_view_count(self, page_id: int) -> None:
        """Incrementa contador de visualizações"""
        pass

class INavigationRepository(ABC):
    """Interface para repositório de navegação"""
    
    @abstractmethod
    def get_main_navigation(self) -> QuerySet:
        """Obtém itens de navegação principal"""
        pass
    
    @abstractmethod
    def create_item(self, item_data: Dict[str, Any]):
        """Cria item de navegação"""
        pass
    
    @abstractmethod
    def update_item(self, item_id: int, item_data: Dict[str, Any]):
        """Atualiza item de navegação"""
        pass
    
    @abstractmethod
    def delete_item(self, item_id: int) -> bool:
        """Deleta item de navegação"""
        pass
    
    @abstractmethod
    def update_order(self, item_id: int, new_order: int) -> bool:
        """Atualiza ordem do item"""
        pass
    
    @abstractmethod
    def get_children(self, parent_id: int) -> QuerySet:
        """Obtém itens filhos"""
        pass

class ISEORepository(ABC):
    """Interface para repositório de SEO"""
    
    @abstractmethod
    def get_settings(self):
        """Obtém configurações de SEO"""
        pass
    
    @abstractmethod
    def update_settings(self, seo_data: Dict[str, Any]):
        """Atualiza configurações de SEO"""
        pass
    
    @abstractmethod
    def create_settings(self, seo_data: Dict[str, Any]):
        """Cria configurações de SEO"""
        pass

class IAnalyticsRepository(ABC):
    """Interface para repositório de analytics"""
    
    @abstractmethod
    def create_page_view(self, page_id: int, ip_address: str, user_agent: str) -> None:
        """Registra visualização de página"""
        pass
    
    @abstractmethod
    def get_page_views(self, page_id: int, days: int = 30) -> int:
        """Obtém número de visualizações"""
        pass
    
    @abstractmethod
    def get_popular_pages(self, days: int = 30, limit: int = 10) -> QuerySet:
        """Obtém páginas mais populares"""
        pass
    
    @abstractmethod
    def get_analytics_data(self, page_id: int, days: int = 30) -> Dict[str, Any]:
        """Obtém dados de analytics"""
        pass
