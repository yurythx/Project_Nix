from typing import Dict, Any, Optional
from django.db.models import QuerySet
from django.db import transaction
from django.contrib.auth import get_user_model
from apps.articles.interfaces.services import IArticleService
from apps.articles.interfaces.repositories import IArticleRepository
import logging
from core.observers import event_dispatcher, Event
from datetime import datetime

User = get_user_model()
logger = logging.getLogger(__name__)

class ArticleService(IArticleService):
    """Serviço para gerenciamento de artigos"""
    
    def __init__(self, article_repository: IArticleRepository):
        self.article_repository = article_repository
    
    def get_published_articles(self, limit: Optional[int] = None) -> QuerySet:
        """
        Obtém artigos publicados
        :param limit: Limite de resultados
        :return: QuerySet de artigos publicados
        """
        return self.article_repository.list_published(limit)
    
    def get_article_by_slug(self, slug: str):
        """
        Obtém artigo por slug
        :param slug: Slug do artigo
        :return: Artigo encontrado
        """
        return self.article_repository.get_by_slug(slug)
    
    def get_featured_articles(self, limit: int = 5) -> QuerySet:
        """
        Obtém artigos em destaque
        :param limit: Limite de resultados
        :return: QuerySet de artigos em destaque
        """
        return self.article_repository.list_featured(limit)
    
    @transaction.atomic
    def create_article(self, article_data: Dict[str, Any], author: User):
        """
        Cria um novo artigo
        :param article_data: Dados do artigo
        :param author: Autor do artigo
        :return: Artigo criado
        """
        # Validações
        title = article_data.get('title')
        if not title:
            raise ValueError("Título é obrigatório")
        
        excerpt = article_data.get('excerpt')
        if not excerpt:
            raise ValueError("Resumo é obrigatório")
        
        content = article_data.get('content')
        if not content:
            raise ValueError("Conteúdo é obrigatório")
        
        slug = article_data.get('slug')
        if slug and self.article_repository.exists_by_slug(slug):
            raise ValueError(f"Já existe um artigo com o slug '{slug}'")
        
        # Adiciona autor
        article_data['author'] = author
        
        # Cria o artigo
        article = self.article_repository.create(article_data)
        
        # Dispara evento para observers
        event = Event(
            name='article_created',
            data=article,
            timestamp=datetime.now(),
            source='article_service'
        )
        event_dispatcher.dispatch(event)
        
        logger.info(f"Artigo criado: {article.title} por {author.email}")
        return article
    
    @transaction.atomic
    def update_article(self, article_id: int, article_data: Dict[str, Any], updated_by: User):
        """
        Atualiza um artigo
        :param article_id: ID do artigo
        :param article_data: Dados para atualização
        :param updated_by: Usuário que está atualizando
        :return: Artigo atualizado
        """
        # Obtém o artigo
        article = self.article_repository.get_by_id(article_id)
        
        # Verifica permissões (autor ou staff)
        if article.author != updated_by and not updated_by.is_staff:
            raise PermissionError("Você não tem permissão para editar este artigo")
        
        # Validações
        slug = article_data.get('slug')
        if slug and slug != article.slug:
            if self.article_repository.exists_by_slug(slug, exclude_id=article_id):
                raise ValueError(f"Já existe um artigo com o slug '{slug}'")
        
        # Atualiza o artigo
        updated_article = self.article_repository.update(article_id, article_data)
        
        logger.info(f"Artigo atualizado: {updated_article.title} por {updated_by.email}")
        return updated_article
    
    @transaction.atomic
    def delete_article(self, article_id: int, deleted_by: User) -> bool:
        """
        Deleta um artigo
        :param article_id: ID do artigo
        :param deleted_by: Usuário que está deletando
        :return: True se deletado com sucesso
        """
        try:
            # Obtém o artigo
            article = self.article_repository.get_by_id(article_id)
            
            # Verifica permissões (autor ou staff)
            if article.author != deleted_by and not deleted_by.is_staff:
                raise PermissionError("Você não tem permissão para deletar este artigo")
            
            # Deleta o artigo
            success = self.article_repository.delete(article_id)
            
            if success:
                logger.info(f"Artigo deletado: {article.title} por {deleted_by.email}")
            
            return success
        except Exception as e:
            logger.error(f"Erro ao deletar artigo {article_id}: {str(e)}")
            raise
    
    def publish_article(self, article_id: int, published_by: User):
        """
        Publica um artigo
        :param article_id: ID do artigo
        :param published_by: Usuário que está publicando
        :return: Artigo publicado
        """
        # Obtém o artigo
        article = self.article_repository.get_by_id(article_id)
        
        # Verifica permissões (autor ou staff)
        if article.author != published_by and not published_by.is_staff:
            raise PermissionError("Você não tem permissão para publicar este artigo")
        
        # Publica o artigo
        published_article = self.article_repository.publish_article(article_id)
        
        logger.info(f"Artigo publicado: {published_article.title} por {published_by.email}")
        return published_article
    
    def search_articles(self, query: str) -> QuerySet:
        """
        Busca artigos por termo
        :param query: Termo de busca
        :return: QuerySet de artigos encontrados
        """
        return self.article_repository.search(query)
    
    def get_articles_by_category(self, category_slug: str) -> QuerySet:
        """
        Obtém artigos por categoria
        :param category_slug: Slug da categoria
        :return: QuerySet de artigos da categoria
        """
        from apps.articles.repositories.category_repository import DjangoCategoryRepository
        
        category_repo = DjangoCategoryRepository()
        category = category_repo.get_by_slug(category_slug)
        
        return self.article_repository.get_by_category(category.id)
    
    def get_articles_by_tag(self, tag_slug: str) -> QuerySet:
        """
        Obtém artigos por tag
        :param tag_slug: Slug da tag
        :return: QuerySet de artigos da tag
        """
        from apps.articles.repositories.tag_repository import DjangoTagRepository
        
        tag_repo = DjangoTagRepository()
        tag = tag_repo.get_by_slug(tag_slug)
        
        return self.article_repository.get_by_tag(tag.id)
    
    def get_articles_by_author(self, author_id: int) -> QuerySet:
        """
        Obtém artigos por autor
        :param author_id: ID do autor
        :return: QuerySet de artigos do autor
        """
        return self.article_repository.get_by_author(author_id)
    
    def increment_article_views(self, article_id: int) -> None:
        """
        Incrementa contador de visualizações
        :param article_id: ID do artigo
        """
        self.article_repository.increment_view_count(article_id)
    
    def get_related_articles(self, article, limit: int = 3) -> QuerySet:
        """
        Obtém artigos relacionados
        :param article: Artigo de referência
        :param limit: Limite de resultados
        :return: QuerySet de artigos relacionados
        """
        return self.article_repository.get_related_articles(article, limit)
