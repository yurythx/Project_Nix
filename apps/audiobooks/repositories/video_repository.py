from typing import Any, Dict, Optional, List
from django.db.models import Q, Count, Avg
from django.db.models.query import QuerySet
from django.core.exceptions import ObjectDoesNotExist
from django.utils.text import slugify

from apps.audiobooks.interfaces.video_repository import VideoRepositoryInterface
from apps.audiobooks.models import VideoAudio, VideoProgress, VideoFavorite
from apps.audiobooks.models.category import Category

class VideoRepository(VideoRepositoryInterface):
    """
    Implementação do repositório de vídeos
    
    Responsável por todas as operações de persistência relacionadas a vídeos.
    Segue o princípio de Responsabilidade Única (S do SOLID) ao lidar apenas com
    operações de acesso a dados para vídeos.
    """
    
    def get_all(self) -> QuerySet:
        """Obtém todos os vídeos"""
        return VideoAudio.objects.all()
    
    def get_by_id(self, video_id: int):
        """Obtém um vídeo por ID"""
        try:
            return VideoAudio.objects.get(pk=video_id)
        except VideoAudio.DoesNotExist:
            return None
    
    def get_by_slug(self, slug: str):
        """Obtém um vídeo por slug"""
        try:
            return VideoAudio.objects.get(slug=slug)
        except VideoAudio.DoesNotExist:
            return None
    
    def search(self, query: str) -> QuerySet:
        """Busca vídeos por título, autor ou descrição"""
        return VideoAudio.objects.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(description__icontains=query)
        )
    
    def create(self, data: Dict[str, Any]):
        """Cria um novo vídeo"""
        return VideoAudio.objects.create(**data)
    
    def update(self, video_id: int, data: Dict[str, Any]):
        """Atualiza um vídeo existente"""
        try:
            video = VideoAudio.objects.get(pk=video_id)
            for key, value in data.items():
                setattr(video, key, value)
            video.save()
            return video
        except VideoAudio.DoesNotExist:
            return None
    
    def delete(self, video_id: int) -> bool:
        """Remove um vídeo"""
        try:
            video = VideoAudio.objects.get(pk=video_id)
            video.delete()
            return True
        except VideoAudio.DoesNotExist:
            return False
    
    def get_by_category(self, category) -> QuerySet:
        """Obtém vídeos por categoria"""
        # Aceita tanto string (slug) quanto objeto Category
        if isinstance(category, Category):
            return VideoAudio.objects.filter(category=category, is_public=True)
        elif isinstance(category, str):
            return VideoAudio.objects.filter(category__slug=category, is_public=True)
        else:
            return VideoAudio.objects.none()
    
    def get_featured(self, limit: int = 5) -> QuerySet:
        """Obtém vídeos em destaque"""
        return VideoAudio.objects.filter(
            is_featured=True, 
            is_public=True
        ).order_by('-created_at')[:limit]
    
    def get_recent(self, limit: int = 5) -> QuerySet:
        """Obtém os vídeos mais recentes"""
        return VideoAudio.objects.filter(
            is_public=True
        ).order_by('-created_at')[:limit]
    
    def get_related_videos(self, video: VideoAudio, limit: int = 6) -> QuerySet:
        """Obtém vídeos relacionados ao vídeo fornecido"""
        # Busca por categoria e autor semelhantes
        return VideoAudio.objects.filter(
            Q(category=video.category) | Q(author=video.author),
            is_public=True
        ).exclude(id=video.id).order_by('-created_at')[:limit]
    
    def get_popular_videos(self, limit: int = 5) -> QuerySet:
        """Obtém os vídeos mais populares baseado em visualizações"""
        return VideoAudio.objects.filter(
            is_public=True
        ).order_by('-views')[:limit]
    
    def get_user_favorites(self, user_id: int) -> QuerySet:
        """Obtém os vídeos favoritos de um usuário"""
        return VideoAudio.objects.filter(
            favorited_by__user_id=user_id,
            is_public=True
        ).order_by('-favorited_by__created_at')
    
    def get_user_progress(self, user_id: int) -> QuerySet:
        """Obtém os vídeos com progresso de um usuário"""
        return VideoAudio.objects.filter(
            videoprogress__user_id=user_id,
            is_public=True
        ).order_by('-videoprogress__last_played')
    
    def get_video_stats(self, video_id: int) -> Dict[str, Any]:
        """Obtém estatísticas de um vídeo"""
        try:
            video = VideoAudio.objects.get(pk=video_id)
            favorites_count = VideoFavorite.objects.filter(video=video).count()
            progress_count = VideoProgress.objects.filter(video=video).count()
            completion_count = VideoProgress.objects.filter(video=video, is_completed=True).count()
            
            return {
                'views': video.views,
                'favorites': favorites_count,
                'started': progress_count,
                'completed': completion_count,
                'completion_rate': (completion_count / progress_count * 100) if progress_count > 0 else 0
            }
        except VideoAudio.DoesNotExist:
            return {}
    
    def toggle_favorite(self, user_id: int, video_id: int) -> bool:
        """Adiciona ou remove um vídeo dos favoritos de um usuário"""
        try:
            video = VideoAudio.objects.get(pk=video_id)
            favorite, created = VideoFavorite.objects.get_or_create(
                user_id=user_id,
                video=video
            )
            
            if not created:
                favorite.delete()
                return False  # Removido dos favoritos
            
            return True  # Adicionado aos favoritos
        except VideoAudio.DoesNotExist:
            return False
