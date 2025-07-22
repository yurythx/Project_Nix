from typing import Dict, Any, Optional
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q, QuerySet, F
from django.utils import timezone
from apps.articles.interfaces.repositories import IArticleRepository
from apps.articles.models import Article

class DjangoArticleRepository(IArticleRepository):
    """Implementação concreta do repositório de artigos para Django"""
    
    def create(self, article_data: Dict[str, Any]) -> Article:
        """Cria um novo artigo"""
        try:
            # Separa campos many-to-many dos dados do artigo
            many_to_many_fields = {}
            article_fields = {}
            
            for field, value in article_data.items():
                if field in ['tags', 'contributors']:
                    many_to_many_fields[field] = value
                else:
                    article_fields[field] = value
            
            # Cria o artigo sem os campos many-to-many
            article = Article.objects.create(**article_fields)
            
            # Adiciona os campos many-to-many após a criação
            for field, value in many_to_many_fields.items():
                if hasattr(article, field) and value:
                    getattr(article, field).set(value)
            
            return article
        except Exception as e:
            raise ValueError(f"Erro ao criar artigo: {str(e)}")
    
    def get_by_id(self, article_id: int) -> Article:
        """Obtém artigo por ID"""
        try:
            return Article.objects.get(id=article_id)
        except Article.DoesNotExist:
            raise ObjectDoesNotExist(f"Artigo com ID {article_id} não encontrado")
    
    def get_by_slug(self, slug: str) -> Article:
        """Obtém artigo por slug"""
        try:
            return Article.objects.select_related('author', 'category').prefetch_related('tags').get(
                slug=slug, 
                status='published'
            )
        except Article.DoesNotExist:
            raise ObjectDoesNotExist(f"Artigo com slug '{slug}' não encontrado")
    
    def update(self, article_id: int, article_data: Dict[str, Any]) -> Article:
        """Atualiza artigo"""
        article = self.get_by_id(article_id)
        
        # Separa campos many-to-many dos dados do artigo
        many_to_many_fields = {}
        article_fields = {}
        
        for field, value in article_data.items():
            if field in ['tags', 'contributors']:
                many_to_many_fields[field] = value
            else:
                article_fields[field] = value
        
        # Atualiza campos normais
        for field, value in article_fields.items():
            if hasattr(article, field):
                setattr(article, field, value)
        
        article.save()
        
        # Atualiza campos many-to-many
        for field, value in many_to_many_fields.items():
            if hasattr(article, field) and value is not None:
                getattr(article, field).set(value)
        
        return article
    
    def delete(self, article_id: int) -> bool:
        """Deleta artigo"""
        try:
            article = self.get_by_id(article_id)
            article.delete()
            return True
        except ObjectDoesNotExist:
            return False
    
    def list_published(self, limit: Optional[int] = None) -> QuerySet:
        """Lista artigos publicados"""
        queryset = Article.objects.filter(
            status='published',
            published_at__lte=timezone.now()
        ).select_related('author', 'category').prefetch_related('tags').order_by('-published_at')
        
        if limit:
            queryset = queryset[:limit]
        
        return queryset
    
    def list_featured(self, limit: int = 5) -> QuerySet:
        """Lista artigos em destaque"""
        return Article.objects.filter(
            status='published',
            is_featured=True,
            published_at__lte=timezone.now()
        ).select_related('author', 'category').order_by('-published_at')[:limit]
    
    def search(self, query: str) -> QuerySet:
        """Busca artigos por termo"""
        if not query:
            return Article.objects.none()
        
        return Article.objects.filter(
            Q(title__icontains=query) |
            Q(excerpt__icontains=query) |
            Q(content__icontains=query) |
            Q(meta_keywords__icontains=query) |
            Q(tags__name__icontains=query),
            status='published',
            published_at__lte=timezone.now()
        ).select_related('author', 'category').prefetch_related('tags').distinct().order_by('-published_at')
    
    def get_by_category(self, category_id: int) -> QuerySet:
        """Obtém artigos por categoria"""
        return Article.objects.filter(
            category_id=category_id,
            status='published',
            published_at__lte=timezone.now()
        ).select_related('author', 'category').prefetch_related('tags').order_by('-published_at')
    
    def get_by_tag(self, tag_id: int) -> QuerySet:
        """Obtém artigos por tag"""
        return Article.objects.filter(
            tags__id=tag_id,
            status='published',
            published_at__lte=timezone.now()
        ).select_related('author', 'category').prefetch_related('tags').order_by('-published_at')
    
    def get_by_author(self, author_id: int) -> QuerySet:
        """Obtém artigos por autor"""
        return Article.objects.filter(
            Q(author_id=author_id) | Q(contributors__id=author_id),
            status='published',
            published_at__lte=timezone.now()
        ).select_related('author', 'category').prefetch_related('tags').distinct().order_by('-published_at')
    
    def increment_view_count(self, article_id: int) -> None:
        """Incrementa contador de visualizações"""
        try:
            Article.objects.filter(id=article_id).update(
                view_count=F('view_count') + 1
            )
        except Exception:
            # Falha silenciosa para não afetar a experiência do usuário
            pass
    
    def get_related_articles(self, article: Article, limit: int = 3) -> QuerySet:
        """Obtém artigos relacionados"""
        related = Article.objects.filter(
            status='published',
            published_at__lte=timezone.now()
        ).exclude(id=article.id)
        
        # Prioriza artigos da mesma categoria
        if article.category:
            related = related.filter(category=article.category)
        
        # Se não há artigos da mesma categoria, busca por tags
        if not related.exists() and article.tags.exists():
            related = Article.objects.filter(
                tags__in=article.tags.all(),
                status='published',
                published_at__lte=timezone.now()
            ).exclude(id=article.id).distinct()
        
        return related.select_related('author', 'category')[:limit]
    
    def list_all(self, filters: Dict[str, Any] = None) -> QuerySet:
        """Lista todos os artigos com filtros opcionais"""
        queryset = Article.objects.all().select_related('author', 'category').prefetch_related('tags')
        
        if filters:
            # Filtro por status
            if 'status' in filters:
                queryset = queryset.filter(status=filters['status'])
            
            # Filtro por autor
            if 'author' in filters:
                queryset = queryset.filter(author=filters['author'])
            
            # Filtro por categoria
            if 'category' in filters:
                queryset = queryset.filter(category=filters['category'])
            
            # Filtro por data
            if 'date_from' in filters:
                queryset = queryset.filter(published_at__gte=filters['date_from'])
            
            if 'date_to' in filters:
                queryset = queryset.filter(published_at__lte=filters['date_to'])
        
        return queryset.order_by('-created_at')
    
    def exists_by_slug(self, slug: str, exclude_id: int = None) -> bool:
        """Verifica se existe artigo com o slug"""
        queryset = Article.objects.filter(slug=slug)
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)
        return queryset.exists()
    
    def publish_article(self, article_id: int) -> Article:
        """Publica um artigo"""
        article = self.get_by_id(article_id)
        article.status = 'published'
        if not article.published_at:
            article.published_at = timezone.now()
        article.save()
        return article
    
    def unpublish_article(self, article_id: int) -> Article:
        """Despublica um artigo"""
        article = self.get_by_id(article_id)
        article.status = 'draft'
        article.save()
        return article
