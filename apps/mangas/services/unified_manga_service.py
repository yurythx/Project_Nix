import os
import logging
import zipfile
import rarfile
from typing import List, Dict, Optional, Tuple, Any
from django.core.files.uploadedfile import UploadedFile
from django.core.cache import cache
from django.db import transaction
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from PIL import Image
import tempfile
import shutil

from apps.mangas.models import Manga, Volume, Capitulo, Pagina
from apps.mangas.validators import (
    ImageFileValidator,
    ArchiveFileValidator
)
from apps.mangas.constants.file_limits import (
    CACHE_KEYS,
    MAX_PAGES_PER_CHAPTER,
    ALLOWED_IMAGE_EXTENSIONS,
    ERROR_MESSAGES
)

logger = logging.getLogger(__name__)

# Definir CACHE_TIMEOUT localmente (não existe no file_limits.py)
CACHE_TIMEOUT = 3600  # 1 hora

class UnifiedMangaService:
    """Serviço unificado para operações de mangá com cache inteligente."""
    
    def __init__(self):
        self.cache_timeout = CACHE_TIMEOUT
    
    def create_manga(self, data: Dict[str, Any], cover_image: Optional[UploadedFile] = None) -> Manga:
        """Cria um novo mangá com validação e cache."""
        try:
            with transaction.atomic():
                # Validar dados obrigatórios
                if not data.get('title'):
                    raise ValidationError("Título é obrigatório")
                
                # Criar slug único
                slug = slugify(data['title'])
                if Manga.objects.filter(slug=slug).exists():
                    counter = 1
                    while Manga.objects.filter(slug=f"{slug}-{counter}").exists():
                        counter += 1
                    slug = f"{slug}-{counter}"
                
                # Criar mangá
                manga = Manga.objects.create(
                    title=data['title'],
                    author=data.get('author', ''),
                    description=data.get('description', ''),
                    slug=slug,
                    cover_image=cover_image
                )
                
                # Invalidar cache
                self._invalidate_manga_cache()
                
                logger.info(f"Mangá criado: {manga.title} (ID: {manga.id})")
                return manga
                
        except Exception as e:
            logger.error(f"Erro ao criar mangá: {str(e)}")
            raise ValidationError(f"Erro ao criar mangá: {str(e)}")
    
    def get_manga_with_cache(self, manga_id: int) -> Optional[Manga]:
        """Obtém mangá por ID com cache."""
        cache_key = f"manga_detail_{manga_id}"
        
        # Tentar buscar no cache
        manga = cache.get(cache_key)
        if manga:
            return manga
        
        # Buscar no banco de dados
        try:
            manga = Manga.objects.select_related().prefetch_related(
                'volumes__capitulos__paginas'
            ).get(id=manga_id, is_published=True)
            
            # Armazenar no cache
            cache.set(cache_key, manga, self.cache_timeout)
            return manga
            
        except Manga.DoesNotExist:
            return None
    
    def get_manga_by_slug_with_cache(self, slug: str) -> Optional[Manga]:
        """Obtém mangá por slug com cache."""
        cache_key = f"manga_slug_{slug}"
        
        # Tentar buscar no cache
        manga = cache.get(cache_key)
        if manga:
            return manga
        
        # Buscar no banco de dados
        try:
            manga = Manga.objects.select_related().prefetch_related(
                'volumes__capitulos__paginas'
            ).get(slug=slug, is_published=True)
            
            # Armazenar no cache
            cache.set(cache_key, manga, self.cache_timeout)
            return manga
            
        except Manga.DoesNotExist:
            return None
    
    def get_manga_stats(self, manga: Manga) -> Dict[str, Any]:
        """Obtém estatísticas do mangá com cache."""
        cache_key = f"manga_stats_{manga.id}"
        
        # Tentar buscar no cache
        stats = cache.get(cache_key)
        if stats:
            return stats
        
        # Calcular estatísticas
        stats = {
            'total_volumes': manga.volumes.count(),
            'total_chapters': sum(volume.capitulos.count() for volume in manga.volumes.all()),
            'total_pages': sum(
                sum(capitulo.paginas.count() for capitulo in volume.capitulos.all())
                for volume in manga.volumes.all()
            ),
            'view_count': manga.view_count,
            'is_published': manga.is_published,
            'created_at': manga.created_at.isoformat() if manga.created_at else None,
            'updated_at': manga.updated_at.isoformat() if manga.updated_at else None,
        }
        
        # Armazenar no cache
        cache.set(cache_key, stats, self.cache_timeout)
        return stats
    
    def _invalidate_manga_cache(self, manga_id: Optional[int] = None):
        """Invalida cache relacionado a mangás."""
        if manga_id:
            # Invalidar cache específico do mangá
            cache.delete(f"manga_detail_{manga_id}")
            cache.delete(f"manga_stats_{manga_id}")
            
            # Buscar slug para invalidar cache por slug
            try:
                manga = Manga.objects.get(id=manga_id)
                cache.delete(f"manga_slug_{manga.slug}")
            except Manga.DoesNotExist:
                pass
        
        # Invalidar cache geral
        cache.delete('manga_list')
        cache.delete('latest_manga_updates')
        cache.delete('manga_stats')

# Instância global do serviço
unified_manga_service = UnifiedMangaService()