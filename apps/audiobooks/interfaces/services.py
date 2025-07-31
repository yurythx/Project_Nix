from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from django.db.models import QuerySet
from django.contrib.auth import get_user_model

User = get_user_model()

class IVideoAudioService(ABC):
    """Interface para serviços de vídeos como áudio livros"""
    
    @abstractmethod
    def get_all_videos(self, limit: Optional[int] = None) -> QuerySet:
        """
        Obtém todos os vídeos
        :param limit: Limite de resultados
        :return: QuerySet de vídeos
        """
        pass
    
    @abstractmethod
    def get_video_by_slug(self, slug: str):
        """
        Obtém vídeo por slug
        :param slug: Slug do vídeo
        :return: Vídeo encontrado
        """
        pass
    
    @abstractmethod
    def search_videos(self, query: str) -> QuerySet:
        """
        Busca vídeos por título, autor ou descrição
        :param query: Termo de busca
        :return: QuerySet de vídeos encontrados
        """
        pass
    
    @abstractmethod
    def create_video(self, video_data: Dict[str, Any], created_by: User):
        """
        Cria um novo vídeo
        :param video_data: Dados do vídeo
        :param created_by: Usuário que está criando
        :return: Vídeo criado
        """
        pass
    
    @abstractmethod
    def update_video(self, video_id: int, video_data: Dict[str, Any], updated_by: User):
        """
        Atualiza um vídeo
        :param video_id: ID do vídeo
        :param video_data: Dados para atualização
        :param updated_by: Usuário que está atualizando
        :return: Vídeo atualizado
        """
        pass
    
    @abstractmethod
    def delete_video(self, video_id: int, deleted_by: User) -> bool:
        """
        Deleta um vídeo
        :param video_id: ID do vídeo
        :param deleted_by: Usuário que está deletando
        :return: True se deletado com sucesso
        """
        pass
    
    @abstractmethod
    def get_videos_by_category(self, category: str) -> QuerySet:
        """
        Obtém vídeos por categoria
        :param category: Categoria dos vídeos
        :return: QuerySet de vídeos da categoria
        """
        pass
    
    @abstractmethod
    def get_featured_videos(self, limit: int = 5) -> QuerySet:
        """
        Obtém vídeos em destaque
        :param limit: Número máximo de vídeos a retornar
        :return: QuerySet de vídeos em destaque
        """
        pass
    
    @abstractmethod
    def get_recent_videos(self, limit: int = 5) -> QuerySet:
        """
        Obtém os vídeos mais recentes
        :param limit: Número máximo de vídeos a retornar
        :return: QuerySet dos vídeos mais recentes
        """
        pass