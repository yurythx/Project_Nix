from typing import Any, Dict, Optional
from django.db.models import Q
from django.db.models.query import QuerySet
from django.core.exceptions import ObjectDoesNotExist

from apps.audiobooks.interfaces.video_repository import VideoRepositoryInterface
from apps.audiobooks.models import VideoAudio

class VideoRepository(VideoRepositoryInterface):
    """
    Implementação do repositório de vídeos
    
    Responsável por todas as operações de persistência relacionadas a vídeos.
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
    
    def get_by_category(self, category: str) -> QuerySet:
        """Obtém vídeos por categoria"""
        return VideoAudio.objects.filter(category=category, is_public=True)
    
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
