from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from django.core.files.uploadedfile import UploadedFile
from apps.mangas.models import Manga

class MangaServiceInterface(ABC):
    """Interface para serviços de mangá."""
    
    @abstractmethod
    def create_manga(self, data: Dict[str, Any], cover_image: Optional[UploadedFile] = None) -> Manga:
        pass
    
    @abstractmethod
    def get_manga_with_cache(self, manga_id: int) -> Optional[Manga]:
        pass
    
    @abstractmethod
    def get_manga_stats(self, manga: Manga) -> Dict[str, Any]:
        pass