from typing import List, Dict, Any, Optional
from django.db.models import QuerySet
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from apps.audiobooks.interfaces.services import IVideoAudioService
from apps.audiobooks.repositories.video_repository import VideoRepository
from apps.audiobooks.models import VideoAudio

User = get_user_model()

class VideoAudioService(IVideoAudioService):
    """
    Service para operações de vídeos como áudio livros
    
    Princípios SOLID aplicados:
    - Single Responsibility: Apenas operações de vídeos
    - Dependency Inversion: Depende da interface IVideoAudioService
    - Open/Closed: Extensível via herança
    """
    
    def __init__(self, repository: VideoRepository = None):
        """
        Inicializa o service com injeção de dependência
        
        :param repository: Repository para acesso a dados
        """
        self.repository = repository or VideoRepository()
    
    def get_all_videos(self, limit: Optional[int] = None) -> QuerySet:
        """Obtém todos os vídeos"""
        videos = self.repository.get_all()
        if limit:
            videos = videos[:limit]
        return videos
    
    def get_video_by_slug(self, slug: str):
        """Obtém vídeo por slug"""
        try:
            return self.repository.get_by_slug(slug)
        except ObjectDoesNotExist:
            return None
    
    def search_videos(self, query: str) -> QuerySet:
        """Busca vídeos por título, autor ou descrição"""
        return self.repository.search(query)
    
    def create_video(self, video_data: Dict[str, Any], created_by: User):
        """Cria um novo vídeo"""
        # Validações de negócio
        if not video_data.get('title'):
            raise ValueError("Título é obrigatório")
        
        # Adiciona usuário criador
        video_data['created_by'] = created_by
        
        return self.repository.create(video_data)
    
    def update_video(self, video_id: int, video_data: Dict[str, Any], updated_by: User):
        """Atualiza um vídeo"""
        # Validações de negócio
        if not video_data.get('title'):
            raise ValueError("Título é obrigatório")
        
        # Adiciona usuário que atualizou
        video_data['updated_by'] = updated_by
        
        return self.repository.update(video_id, video_data)
    
    def delete_video(self, video_id: int, deleted_by: User) -> bool:
        """Deleta um vídeo"""
        try:
            return self.repository.delete(video_id)
        except ObjectDoesNotExist:
            return False
    
    def get_videos_by_category(self, category: str) -> QuerySet:
        """Obtém vídeos por categoria"""
        return self.repository.get_by_category(category)
    
    def get_featured_videos(self, limit: int = 5) -> QuerySet:
        """Obtém vídeos em destaque"""
        return self.repository.get_featured(limit)
    
    def get_recent_videos(self, limit: int = 5) -> QuerySet:
        """Obtém os vídeos mais recentes"""
        return self.repository.get_recent(limit)
