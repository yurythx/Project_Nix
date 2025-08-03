from typing import List, Dict, Any, Optional
from django.db.models import QuerySet
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.text import slugify
from django.db import transaction

from apps.audiobooks.interfaces.services import IVideoAudioService
from apps.audiobooks.repositories.video_repository import VideoRepository
from apps.audiobooks.models import VideoAudio, VideoProgress, VideoFavorite

User = get_user_model()

class VideoAudioService(IVideoAudioService):
    """
    Service para operações de vídeos como áudio livros
    
    Princípios SOLID aplicados:
    - Single Responsibility: Apenas operações de vídeos
    - Open/Closed: Extensível via herança
    - Liskov Substitution: Implementa corretamente a interface IVideoAudioService
    - Interface Segregation: Usa apenas os métodos necessários da interface
    - Dependency Inversion: Depende de abstrações (interfaces) e não de implementações concretas
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
    
    def get_videos_by_category(self, category) -> QuerySet:
        """Obtém vídeos por categoria (aceita string ou objeto Category)"""
        return self.repository.get_by_category(category)
    
    def get_featured_videos(self, limit: int = 5) -> QuerySet:
        """Obtém vídeos em destaque"""
        return self.repository.get_featured(limit)
    
    def get_recent_videos(self, limit: int = 5) -> QuerySet:
        """Obtém os vídeos mais recentes"""
        return self.repository.get_recent(limit)
    
    def get_related_videos(self, video: VideoAudio, limit: int = 6) -> QuerySet:
        """Obtém vídeos relacionados ao vídeo fornecido"""
        return self.repository.get_related_videos(video, limit)
    
    def get_popular_videos(self, limit: int = 5) -> QuerySet:
        """Obtém os vídeos mais populares baseado em visualizações"""
        return self.repository.get_popular_videos(limit)
    
    def get_user_favorites(self, user: User) -> QuerySet:
        """Obtém os vídeos favoritos de um usuário"""
        return self.repository.get_user_favorites(user.id)
    
    def get_user_progress(self, user: User) -> QuerySet:
        """Obtém os vídeos com progresso de um usuário"""
        return self.repository.get_user_progress(user.id)
    
    def get_video_stats(self, video_id: int) -> Dict[str, Any]:
        """Obtém estatísticas de um vídeo"""
        return self.repository.get_video_stats(video_id)
    
    def toggle_favorite(self, user: User, video_id: int) -> bool:
        """Adiciona ou remove um vídeo dos favoritos de um usuário"""
        return self.repository.toggle_favorite(user.id, video_id)
    
    def update_progress(self, user: User, video_id: int, current_time: float, is_completed: bool = False) -> bool:
        """Atualiza o progresso de um usuário em um vídeo"""
        try:
            video = self.repository.get_by_id(video_id)
            if not video:
                return False
                
            progress, created = VideoProgress.objects.get_or_create(
                user=user,
                video=video,
                defaults={'current_time': current_time, 'is_completed': is_completed}
            )
            
            if not created:
                progress.current_time = current_time
                progress.is_completed = is_completed
                progress.save()
                
            return True
        except Exception:
            return False
