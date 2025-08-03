"""
Service para operações com categorias
Implementa princípios SOLID
"""
from typing import Optional
from django.db.models import QuerySet
from django.core.exceptions import ObjectDoesNotExist

from apps.articles.interfaces.services import ICategoryService
from apps.articles.models.category import Category
from apps.articles.models.article import Article


class CategoryService(ICategoryService):
    """
    Service para operações com categorias
    
    Princípios SOLID aplicados:
    - Single Responsibility: Apenas operações de categorias
    - Dependency Inversion: Pode usar repository injetado
    """
    
    def __init__(self, category_repository=None):
        """
        Inicializa service com repository opcional
        
        Args:
            category_repository: Repository para categorias (opcional)
        """
        self.category_repository = category_repository
    
    def get_categories_with_articles(self) -> QuerySet[Category]:
        """
        Retorna categorias que possuem artigos publicados
        
        Returns:
            QuerySet de categorias com artigos
        """
        return Category.objects.filter(
            articles__status='published',
            is_active=True
        ).distinct().order_by('name')
    
    def get_category_by_slug(self, slug: str) -> Category:
        """
        Busca categoria por slug
        
        Args:
            slug: Slug da categoria
            
        Returns:
            Categoria encontrada
            
        Raises:
            ObjectDoesNotExist: Se categoria não for encontrada
        """
        try:
            return Category.objects.get(slug=slug, is_active=True)
        except Category.DoesNotExist:
            raise ObjectDoesNotExist(f"Categoria com slug '{slug}' não encontrada")
    
    def get_category_articles(self, category: Category) -> QuerySet[Article]:
        """
        Retorna artigos publicados da categoria
        
        Args:
            category: Categoria
            
        Returns:
            QuerySet de artigos da categoria
        """
        return Article.objects.filter(
            category=category,
            status='published'
        ).order_by('-published_at')
    
    def get_active_categories(self) -> QuerySet[Category]:
        """
        Obtém categorias ativas (implementação exigida pela interface)
        :return: QuerySet de categorias ativas
        """
        return Category.objects.filter(is_active=True).order_by('name')
    
    def get_category_stats(self, category: Category) -> dict:
        """
        Retorna estatísticas da categoria
        
        Args:
            category: Categoria
            
        Returns:
            Dicionário com estatísticas
        """
        articles = self.get_category_articles(category)
        
        return {
            'total_articles': articles.count(),
            'featured_articles': articles.filter(is_featured=True).count(),
            'recent_articles': articles[:5],
        }
    
    def create_category(self, category_data: dict) -> Category:
        """
        Cria nova categoria
        
        Args:
            category_data: Dados da categoria
            
        Returns:
            Categoria criada
        """
        category = Category.objects.create(**category_data)
        return category
    
    def update_category(self, category_id: int, category_data: dict) -> Category:
        """
        Atualiza categoria existente
        
        Args:
            category_id: ID da categoria
            category_data: Dados para atualização
            
        Returns:
            Categoria atualizada
            
        Raises:
            ObjectDoesNotExist: Se categoria não for encontrada
        """
        try:
            category = Category.objects.get(id=category_id)
            for key, value in category_data.items():
                setattr(category, key, value)
            category.save()
            return category
        except Category.DoesNotExist:
            raise ObjectDoesNotExist(f"Categoria com ID {category_id} não encontrada")
    
    def delete_category(self, category_id: int) -> bool:
        """
        Remove categoria
        
        Args:
            category_id: ID da categoria
            
        Returns:
            True se removida com sucesso
            
        Raises:
            ObjectDoesNotExist: Se categoria não for encontrada
        """
        try:
            category = Category.objects.get(id=category_id)
            category.delete()
            return True
        except Category.DoesNotExist:
            raise ObjectDoesNotExist(f"Categoria com ID {category_id} não encontrada")
    
    def toggle_category_status(self, category_id: int) -> Category:
        """
        Alterna status ativo/inativo da categoria
        
        Args:
            category_id: ID da categoria
            
        Returns:
            Categoria com status alterado
            
        Raises:
            ObjectDoesNotExist: Se categoria não for encontrada
        """
        try:
            category = Category.objects.get(id=category_id)
            category.is_active = not category.is_active
            category.save()
            return category
        except Category.DoesNotExist:
            raise ObjectDoesNotExist(f"Categoria com ID {category_id} não encontrada")
