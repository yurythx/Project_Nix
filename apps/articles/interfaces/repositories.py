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

class ICommentRepository(ABC):
    """Interface para repositório de comentários"""
    
    @abstractmethod
    def create(self, comment_data: Dict[str, Any]):
        """Cria um novo comentário"""
        pass
    
    @abstractmethod
    def get_by_id(self, comment_id: int):
        """Obtém comentário por ID"""
        pass
    
    @abstractmethod
    def update(self, comment_id: int, comment_data: Dict[str, Any]):
        """Atualiza comentário"""
        pass
    
    @abstractmethod
    def delete(self, comment_id: int) -> bool:
        """Deleta comentário"""
        pass
    
    @abstractmethod
    def get_by_article(self, article_id: int) -> QuerySet:
        """Obtém comentários de um artigo"""
        pass
    
    @abstractmethod
    def get_pending_approval(self) -> QuerySet:
        """Obtém comentários pendentes de aprovação"""
        pass
    
    @abstractmethod
    def get_by_user(self, user_id: int) -> QuerySet:
        """Obtém comentários de um usuário"""
        pass
    
    @abstractmethod
    def approve(self, comment_id: int) -> bool:
        """Aprova comentário"""
        pass
    
    @abstractmethod
    def mark_as_spam(self, comment_id: int) -> bool:
        """Marca comentário como spam"""
        pass
