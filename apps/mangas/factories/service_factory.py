"""
Factory para criação de services com injeção de dependência
Implementa padrão Factory e Dependency Injection
"""

from typing import Optional
from django.conf import settings

from ..interfaces.repositories import IMangaRepository
from ..repositories.manga_repository import DjangoMangaRepository
from ..services.manga_service_simple import SimpleMangaService


class ServiceFactory:
    """
    Factory para criação de services com configuração centralizada
    
    Princípios SOLID aplicados:
    - Single Responsibility: Apenas criação de services
    - Dependency Inversion: Usa interfaces para abstrair dependências
    - Open/Closed: Extensível para novos services
    """
    
    _manga_repository: Optional[IMangaRepository] = None
    _manga_service: Optional[SimpleMangaService] = None
    
    @classmethod
    def create_manga_repository(cls) -> IMangaRepository:
        """
        Cria instância do repository de mangás
        
        Returns:
            Instância do repository configurado
        """
        if cls._manga_repository is None:
            cls._manga_repository = DjangoMangaRepository()
        return cls._manga_repository
    
    @classmethod
    def create_manga_service(cls) -> SimpleMangaService:
        """
        Cria instância do service de mangás com dependências injetadas
        
        Returns:
            Instância do service configurado
        """
        if cls._manga_service is None:
            repository = cls.create_manga_repository()
            cls._manga_service = SimpleMangaService(repository=repository)
        return cls._manga_service
    
    @classmethod
    def reset(cls):
        """
        Reseta instâncias (útil para testes)
        """
        cls._manga_repository = None
        cls._manga_service = None


# Instância global do factory
service_factory = ServiceFactory()


# Funções de conveniência para uso direto
def get_manga_service() -> SimpleMangaService:
    """
    Função de conveniência para obter service de mangás
    
    Returns:
        Instância configurada do service
    """
    return service_factory.create_manga_service()


def get_manga_repository() -> IMangaRepository:
    """
    Função de conveniência para obter repository de mangás
    
    Returns:
        Instância configurada do repository
    """
    return service_factory.create_manga_repository()
