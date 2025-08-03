from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from django.db.models import QuerySet

class IArticleRepository(ABC):
    """Interface para repositório de artigos"""
    
    @abstractmethod
    def create(self, article_data: Dict[str, Any]):
        """Cria um novo artigo"""
        pass
    
    @abstractmethod
    def get_by_id(self, article_id: int):
        """Obtém artigo por ID"""
        pass
    
    @abstractmethod
    def get_by_slug(self, slug: str):
        """Obtém artigo por slug"""
        pass
    
    @abstractmethod
    def update(self, article_id: int, article_data: Dict[str, Any]):
        """Atualiza artigo"""
        pass
    
    @abstractmethod
    def delete(self, article_id: int) -> bool:
        """Deleta artigo"""
        pass
    
    @abstractmethod
    def list_published(self, limit: Optional[int] = None) -> QuerySet:
        """Lista artigos publicados"""
        pass
    
    @abstractmethod
    def list_featured(self, limit: int = 5) -> QuerySet:
        """Lista artigos em destaque"""
        pass
    
    @abstractmethod
    def search(self, query: str) -> QuerySet:
        """Busca artigos por termo"""
        pass
    
    @abstractmethod
    def get_by_category(self, category_id: int) -> QuerySet:
        """Obtém artigos por categoria"""
        pass
    
    @abstractmethod
    def get_by_tag(self, tag_id: int) -> QuerySet:
        """Obtém artigos por tag"""
        pass
    
    @abstractmethod
    def get_by_author(self, author_id: int) -> QuerySet:
        """Obtém artigos por autor"""
        pass
    
    @abstractmethod
    def increment_view_count(self, article_id: int) -> None:
        """Incrementa contador de visualizações"""
        pass
    
    @abstractmethod
    def get_related_articles(self, article, limit: int = 3) -> QuerySet:
        """Obtém artigos relacionados"""
        pass
    
    @abstractmethod
    def list_all(self, filters: Dict[str, Any] = None) -> QuerySet:
        """Lista todos os artigos com filtros opcionais"""
        pass
    
    @abstractmethod
    def exists_by_slug(self, slug: str, exclude_id: int = None) -> bool:
        """Verifica se existe artigo com o slug"""
        pass
    
    @abstractmethod
    def publish_article(self, article_id: int):
        """Publica um artigo"""
        pass
    
    @abstractmethod
    def unpublish_article(self, article_id: int):
        """Despublica um artigo"""
        pass

class ICategoryRepository(ABC):
    """Interface para repositório de categorias"""
    
    @abstractmethod
    def create(self, category_data: Dict[str, Any]):
        """Cria uma nova categoria"""
        pass
    
    @abstractmethod
    def get_by_id(self, category_id: int):
        """Obtém categoria por ID"""
        pass
    
    @abstractmethod
    def get_by_slug(self, slug: str):
        """Obtém categoria por slug"""
        pass
    
    @abstractmethod
    def update(self, category_id: int, category_data: Dict[str, Any]):
        """Atualiza categoria"""
        pass
    
    @abstractmethod
    def delete(self, category_id: int) -> bool:
        """Deleta categoria"""
        pass
    
    @abstractmethod
    def list_active(self) -> QuerySet:
        """Lista categorias ativas"""
        pass
    
    @abstractmethod
    def get_with_article_count(self) -> QuerySet:
        """Obtém categorias com contagem de artigos"""
        pass

class ITagRepository(ABC):
    """Interface para repositório de tags"""
    
    @abstractmethod
    def create(self, tag_data: Dict[str, Any]):
        """Cria uma nova tag"""
        pass
    
    @abstractmethod
    def get_by_id(self, tag_id: int):
        """Obtém tag por ID"""
        pass
    
    @abstractmethod
    def get_by_slug(self, slug: str):
        """Obtém tag por slug"""
        pass
    
    @abstractmethod
    def update(self, tag_id: int, tag_data: Dict[str, Any]):
        """Atualiza tag"""
        pass
    
    @abstractmethod
    def delete(self, tag_id: int) -> bool:
        """Deleta tag"""
        pass
    
    @abstractmethod
    def list_all(self) -> QuerySet:
        """Lista todas as tags"""
        pass
    
    @abstractmethod
    def get_popular(self, limit: int = 20) -> QuerySet:
        """Obtém tags mais populares"""
        pass
    
    @abstractmethod
    def get_featured(self) -> QuerySet:
        """Obtém tags em destaque"""
        pass

# ICommentRepository removido - migrado para apps.comments
