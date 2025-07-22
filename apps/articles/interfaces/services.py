from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from django.db.models import QuerySet
from django.contrib.auth import get_user_model

User = get_user_model()

class IArticleService(ABC):
    """Interface para serviços de artigos"""
    
    @abstractmethod
    def get_published_articles(self, limit: Optional[int] = None) -> QuerySet:
        """
        Obtém artigos publicados
        :param limit: Limite de resultados
        :return: QuerySet de artigos publicados
        """
        pass
    
    @abstractmethod
    def get_article_by_slug(self, slug: str):
        """
        Obtém artigo por slug
        :param slug: Slug do artigo
        :return: Artigo encontrado
        """
        pass
    
    @abstractmethod
    def get_featured_articles(self, limit: int = 5) -> QuerySet:
        """
        Obtém artigos em destaque
        :param limit: Limite de resultados
        :return: QuerySet de artigos em destaque
        """
        pass
    
    @abstractmethod
    def create_article(self, article_data: Dict[str, Any], author: User):
        """
        Cria um novo artigo
        :param article_data: Dados do artigo
        :param author: Autor do artigo
        :return: Artigo criado
        """
        pass
    
    @abstractmethod
    def update_article(self, article_id: int, article_data: Dict[str, Any], updated_by: User):
        """
        Atualiza um artigo
        :param article_id: ID do artigo
        :param article_data: Dados para atualização
        :param updated_by: Usuário que está atualizando
        :return: Artigo atualizado
        """
        pass
    
    @abstractmethod
    def delete_article(self, article_id: int, deleted_by: User) -> bool:
        """
        Deleta um artigo
        :param article_id: ID do artigo
        :param deleted_by: Usuário que está deletando
        :return: True se deletado com sucesso
        """
        pass
    
    @abstractmethod
    def publish_article(self, article_id: int, published_by: User):
        """
        Publica um artigo
        :param article_id: ID do artigo
        :param published_by: Usuário que está publicando
        :return: Artigo publicado
        """
        pass
    
    @abstractmethod
    def search_articles(self, query: str) -> QuerySet:
        """
        Busca artigos por termo
        :param query: Termo de busca
        :return: QuerySet de artigos encontrados
        """
        pass
    
    @abstractmethod
    def get_articles_by_category(self, category_slug: str) -> QuerySet:
        """
        Obtém artigos por categoria
        :param category_slug: Slug da categoria
        :return: QuerySet de artigos da categoria
        """
        pass
    
    @abstractmethod
    def get_articles_by_tag(self, tag_slug: str) -> QuerySet:
        """
        Obtém artigos por tag
        :param tag_slug: Slug da tag
        :return: QuerySet de artigos da tag
        """
        pass
    
    @abstractmethod
    def get_articles_by_author(self, author_id: int) -> QuerySet:
        """
        Obtém artigos por autor
        :param author_id: ID do autor
        :return: QuerySet de artigos do autor
        """
        pass

class ICategoryService(ABC):
    """Interface para serviços de categorias"""
    
    @abstractmethod
    def get_active_categories(self) -> QuerySet:
        """
        Obtém categorias ativas
        :return: QuerySet de categorias ativas
        """
        pass
    
    @abstractmethod
    def get_category_by_slug(self, slug: str):
        """
        Obtém categoria por slug
        :param slug: Slug da categoria
        :return: Categoria encontrada
        """
        pass
    
    @abstractmethod
    def create_category(self, category_data: Dict[str, Any]):
        """
        Cria uma nova categoria
        :param category_data: Dados da categoria
        :return: Categoria criada
        """
        pass
    
    @abstractmethod
    def update_category(self, category_id: int, category_data: Dict[str, Any]):
        """
        Atualiza uma categoria
        :param category_id: ID da categoria
        :param category_data: Dados para atualização
        :return: Categoria atualizada
        """
        pass

class ITagService(ABC):
    """Interface para serviços de tags"""
    
    @abstractmethod
    def get_popular_tags(self, limit: int = 20) -> QuerySet:
        """
        Obtém tags mais populares
        :param limit: Limite de resultados
        :return: QuerySet de tags populares
        """
        pass
    
    @abstractmethod
    def get_tag_by_slug(self, slug: str):
        """
        Obtém tag por slug
        :param slug: Slug da tag
        :return: Tag encontrada
        """
        pass
    
    @abstractmethod
    def create_tag(self, tag_data: Dict[str, Any]):
        """
        Cria uma nova tag
        :param tag_data: Dados da tag
        :return: Tag criada
        """
        pass

class ICommentService(ABC):
    """Interface para serviços de comentários"""
    
    @abstractmethod
    def get_article_comments(self, article_id: int) -> QuerySet:
        """
        Obtém comentários de um artigo
        :param article_id: ID do artigo
        :return: QuerySet de comentários aprovados
        """
        pass
    
    @abstractmethod
    def create_comment(self, comment_data: Dict[str, Any], request=None):
        """
        Cria um novo comentário
        :param comment_data: Dados do comentário
        :param request: Request HTTP para capturar IP
        :return: Comentário criado
        """
        pass
    
    @abstractmethod
    def approve_comment(self, comment_id: int, approved_by: User):
        """
        Aprova um comentário
        :param comment_id: ID do comentário
        :param approved_by: Usuário que está aprovando
        :return: Comentário aprovado
        """
        pass
    
    @abstractmethod
    def mark_comment_as_spam(self, comment_id: int, marked_by: User):
        """
        Marca comentário como spam
        :param comment_id: ID do comentário
        :param marked_by: Usuário que está marcando
        :return: Comentário marcado
        """
        pass
