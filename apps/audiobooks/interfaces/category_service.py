from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from django.db.models import QuerySet

from apps.audiobooks.models.category import Category

class ICategoryService(ABC):
    """
    Interface para serviço de categorias
    
    Princípios SOLID aplicados:
    - Interface Segregation: Interface específica para operações de categorias
    - Dependency Inversion: Permite injeção de dependência
    """
    
    @abstractmethod
    def get_all_categories(self) -> QuerySet:
        """Retorna todas as categorias"""
        pass
    
    @abstractmethod
    def get_active_categories(self) -> QuerySet:
        """Retorna apenas categorias ativas"""
        pass
    
    @abstractmethod
    def get_category_by_slug(self, slug: str) -> Optional[Category]:
        """Obtém categoria por slug"""
        pass
    
    @abstractmethod
    def get_category_by_id(self, category_id: int) -> Optional[Category]:
        """Obtém categoria por ID"""
        pass
    
    @abstractmethod
    def create_category(self, data: Dict[str, Any]) -> Category:
        """Cria uma nova categoria"""
        pass
    
    @abstractmethod
    def update_category(self, category_id: int, data: Dict[str, Any]) -> bool:
        """Atualiza uma categoria existente"""
        pass
    
    @abstractmethod
    def delete_category(self, category_id: int) -> bool:
        """Exclui uma categoria"""
        pass
    
    @abstractmethod
    def get_categories_with_videos(self) -> QuerySet:
        """Retorna categorias que possuem vídeos"""
        pass