from typing import List, Dict, Any, Optional, Union
from django.db.models import QuerySet, Count
from django.core.exceptions import ObjectDoesNotExist

from apps.audiobooks.interfaces.category_service import ICategoryService
from apps.audiobooks.models.category import Category

class CategoryService(ICategoryService):
    """
    Implementação do serviço de categorias
    
    Princípios SOLID aplicados:
    - Single Responsibility: Apenas operações de categorias
    - Open/Closed: Extensível via herança
    - Liskov Substitution: Implementa completamente a interface ICategoryService
    - Dependency Inversion: Depende de abstrações, não implementações concretas
    """
    
    def get_all_categories(self) -> QuerySet:
        """Retorna todas as categorias"""
        return Category.objects.all()
    
    def get_active_categories(self) -> QuerySet:
        """Retorna apenas categorias ativas"""
        return Category.objects.filter(is_active=True)
    
    def get_category_by_slug(self, slug: str) -> Optional[Category]:
        """Obtém categoria por slug"""
        try:
            return Category.objects.get(slug=slug)
        except ObjectDoesNotExist:
            return None
    
    def get_category_by_id(self, category_id: int) -> Optional[Category]:
        """Obtém categoria por ID"""
        try:
            return Category.objects.get(id=category_id)
        except ObjectDoesNotExist:
            return None
    
    def create_category(self, data: Dict[str, Any]) -> Category:
        """Cria uma nova categoria"""
        category = Category(**data)
        category.save()
        return category
    
    def update_category(self, category_id: int, data: Dict[str, Any]) -> bool:
        """Atualiza uma categoria existente"""
        try:
            category = Category.objects.get(id=category_id)
            for key, value in data.items():
                setattr(category, key, value)
            category.save()
            return True
        except ObjectDoesNotExist:
            return False
    
    def delete_category(self, category_id: int) -> bool:
        """Exclui uma categoria"""
        try:
            category = Category.objects.get(id=category_id)
            category.delete()
            return True
        except ObjectDoesNotExist:
            return False
    
    def get_categories_with_videos(self) -> QuerySet:
        """Retorna categorias que possuem vídeos"""
        return Category.objects.annotate(
            videos_count=Count('videos')
        ).filter(videos_count__gt=0, is_active=True)