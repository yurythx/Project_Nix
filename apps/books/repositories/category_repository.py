from typing import List, Dict, Any, Optional, Union
from django.db.models import QuerySet, Count
from django.core.exceptions import ObjectDoesNotExist

from apps.books.models.category import Category

class CategoryRepository:
    """
    Repositório para operações de dados de categorias
    
    Princípios SOLID aplicados:
    - Single Responsibility: Apenas acesso a dados de categorias
    - Open/Closed: Extensível via herança
    """
    
    def get_all(self) -> QuerySet:
        """Retorna todas as categorias"""
        return Category.objects.all()
    
    def get_active(self) -> QuerySet:
        """Retorna apenas categorias ativas"""
        return Category.objects.filter(is_active=True)
    
    def get_by_slug(self, slug: str) -> Optional[Category]:
        """Obtém categoria por slug"""
        try:
            return Category.objects.get(slug=slug)
        except ObjectDoesNotExist:
            return None
    
    def get_by_id(self, category_id: int) -> Optional[Category]:
        """Obtém categoria por ID"""
        try:
            return Category.objects.get(id=category_id)
        except ObjectDoesNotExist:
            return None
    
    def create(self, data: Dict[str, Any]) -> Category:
        """Cria uma nova categoria"""
        category = Category(**data)
        category.save()
        return category
    
    def update(self, category_id: int, data: Dict[str, Any]) -> bool:
        """Atualiza uma categoria existente"""
        try:
            category = Category.objects.get(id=category_id)
            for key, value in data.items():
                setattr(category, key, value)
            category.save()
            return True
        except ObjectDoesNotExist:
            return False
    
    def delete(self, category_id: int) -> bool:
        """Exclui uma categoria"""
        try:
            category = Category.objects.get(id=category_id)
            category.delete()
            return True
        except ObjectDoesNotExist:
            return False
    
    def get_with_books(self) -> QuerySet:
        """Retorna categorias que possuem livros"""
        return Category.objects.filter(
            is_active=True,
            books__is_public=True
        ).annotate(
            books_count=Count('books')
        ).filter(
            books_count__gt=0
        ).distinct()
    
    def get_by_name(self, name: str) -> Optional[Category]:
        """Obtém categoria por nome"""
        try:
            return Category.objects.get(name__iexact=name)
        except ObjectDoesNotExist:
            return None