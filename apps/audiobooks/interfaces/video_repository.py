from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from django.db.models import QuerySet, Q

class VideoRepositoryInterface(ABC):
    """Interface para repositórios de vídeos"""
    
    @abstractmethod
    def get_all(self) -> QuerySet:
        """
        Obtém todos os vídeos
        :return: QuerySet de vídeos
        """
        pass
    
    @abstractmethod
    def get_by_id(self, video_id: int):
        """
        Obtém um vídeo por ID
        :param video_id: ID do vídeo
        :return: Instância do vídeo ou None se não encontrado
        """
        pass
    
    @abstractmethod
    def get_by_slug(self, slug: str):
        """
        Obtém um vídeo por slug
        :param slug: Slug do vídeo
        :return: Instância do vídeo ou None se não encontrado
        """
        pass
    
    @abstractmethod
    def search(self, query: str) -> QuerySet:
        """
        Busca vídeos por título, autor ou descrição
        :param query: Termo de busca
        :return: QuerySet de vídeos encontrados
        """
        pass
    
    @abstractmethod
    def create(self, data: Dict[str, Any]):
        """
        Cria um novo vídeo
        :param data: Dados do vídeo
        :return: Instância do vídeo criado
        """
        pass
    
    @abstractmethod
    def update(self, video_id: int, data: Dict[str, Any]):
        """
        Atualiza um vídeo existente
        :param video_id: ID do vídeo a ser atualizado
        :param data: Dados para atualização
        :return: Instância do vídeo atualizado ou None se não encontrado
        """
        pass
    
    @abstractmethod
    def delete(self, video_id: int) -> bool:
        """
        Remove um vídeo
        :param video_id: ID do vídeo a ser removido
        :return: True se removido com sucesso, False caso contrário
        """
        pass
    
    @abstractmethod
    def get_by_category(self, category: str) -> QuerySet:
        """
        Obtém vídeos por categoria
        :param category: Categoria dos vídeos
        :return: QuerySet de vídeos da categoria
        """
        pass
    
    @abstractmethod
    def get_featured(self, limit: int = 5) -> QuerySet:
        """
        Obtém vídeos em destaque
        :param limit: Número máximo de vídeos a retornar
        :return: QuerySet de vídeos em destaque
        """
        pass
    
    @abstractmethod
    def get_recent(self, limit: int = 5) -> QuerySet:
        """
        Obtém os vídeos mais recentes
        :param limit: Número máximo de vídeos a retornar
        :return: QuerySet dos vídeos mais recentes
        """
        pass
