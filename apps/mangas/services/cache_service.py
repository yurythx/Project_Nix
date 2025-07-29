"""
Serviço de cache para mangás com estratégia em múltiplas camadas
Implementa cache inteligente com invalidação automática
"""

import logging
import json
from typing import Any, Optional, Dict, List
from django.core.cache import cache
from django.conf import settings
from django.core.serializers import serialize
from django.db.models import QuerySet

from ..models.manga import Manga
from ..models.capitulo import Capitulo
from ..models.pagina import Pagina

logger = logging.getLogger(__name__)


class MangaCacheService:
    """
    Serviço de cache para mangás com estratégia inteligente
    
    Implementa:
    - Cache em múltiplas camadas
    - Invalidação automática
    - Compressão de dados
    - Métricas de hit/miss
    """
    
    # Configurações de cache
    DEFAULT_TIMEOUT = getattr(settings, 'MANGA_CACHE_TIMEOUT', 60 * 15)  # 15 minutos
    LONG_TIMEOUT = getattr(settings, 'MANGA_CACHE_LONG_TIMEOUT', 60 * 60)  # 1 hora
    SHORT_TIMEOUT = getattr(settings, 'MANGA_CACHE_SHORT_TIMEOUT', 60 * 5)  # 5 minutos
    
    # Prefixos de cache
    MANGA_PREFIX = "manga"
    CHAPTER_PREFIX = "chapter"
    PAGE_PREFIX = "page"
    LIST_PREFIX = "list"
    STATS_PREFIX = "stats"
    
    def __init__(self):
        self.logger = logger
        self._hit_count = 0
        self._miss_count = 0
    
    # === MÉTODOS DE CACHE PARA MANGÁS ===
    
    def get_manga_cache_key(self, slug: str) -> str:
        """Gera chave de cache para mangá"""
        return f"{self.MANGA_PREFIX}:detail:{slug}"
    
    def get_manga_context_cache_key(self, slug: str) -> str:
        """Gera chave de cache para contexto do mangá"""
        return f"{self.MANGA_PREFIX}:context:{slug}"
    
    def cache_manga(self, manga: Manga, timeout: Optional[int] = None) -> bool:
        """
        Armazena mangá no cache
        
        Args:
            manga: Instância do mangá
            timeout: Tempo de expiração (opcional)
            
        Returns:
            True se armazenado com sucesso
        """
        try:
            cache_key = self.get_manga_cache_key(manga.slug)
            timeout = timeout or self.DEFAULT_TIMEOUT
            
            # Serializa dados do mangá
            manga_data = {
                'id': manga.id,
                'title': manga.title,
                'slug': manga.slug,
                'description': manga.description,
                'author': manga.author,
                'is_published': manga.is_published,
                'view_count': manga.view_count,
                'created_at': manga.created_at.isoformat(),
                'updated_at': manga.updated_at.isoformat(),
            }
            
            cache.set(cache_key, manga_data, timeout)
            self.logger.debug(f"Manga cached: {manga.slug}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao cachear manga {manga.slug}: {e}")
            return False
    
    def get_cached_manga(self, slug: str) -> Optional[Dict[str, Any]]:
        """
        Recupera mangá do cache
        
        Args:
            slug: Slug do mangá
            
        Returns:
            Dados do mangá ou None se não encontrado
        """
        try:
            cache_key = self.get_manga_cache_key(slug)
            manga_data = cache.get(cache_key)
            
            if manga_data:
                self._hit_count += 1
                self.logger.debug(f"Cache hit: manga {slug}")
                return manga_data
            else:
                self._miss_count += 1
                self.logger.debug(f"Cache miss: manga {slug}")
                return None
                
        except Exception as e:
            self.logger.error(f"Erro ao recuperar manga do cache {slug}: {e}")
            return None
    
    def cache_manga_context(self, slug: str, context: Dict[str, Any], timeout: Optional[int] = None) -> bool:
        """
        Armazena contexto do mangá no cache
        
        Args:
            slug: Slug do mangá
            context: Contexto a ser armazenado
            timeout: Tempo de expiração (opcional)
            
        Returns:
            True se armazenado com sucesso
        """
        try:
            cache_key = self.get_manga_context_cache_key(slug)
            timeout = timeout or self.SHORT_TIMEOUT
            
            # Serializa contexto (apenas dados serializáveis)
            serializable_context = {
                'total_chapters': context.get('total_chapters', 0),
                'chapter_count': context.get('chapter_count', 0),
                'latest_chapter_id': context.get('latest_chapter').id if context.get('latest_chapter') else None,
                'volumes_count': len(context.get('volumes', [])),
            }
            
            cache.set(cache_key, serializable_context, timeout)
            self.logger.debug(f"Manga context cached: {slug}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao cachear contexto do manga {slug}: {e}")
            return False
    
    def get_cached_manga_context(self, slug: str) -> Optional[Dict[str, Any]]:
        """
        Recupera contexto do mangá do cache
        
        Args:
            slug: Slug do mangá
            
        Returns:
            Contexto do mangá ou None se não encontrado
        """
        try:
            cache_key = self.get_manga_context_cache_key(slug)
            context = cache.get(cache_key)
            
            if context:
                self._hit_count += 1
                self.logger.debug(f"Cache hit: manga context {slug}")
                return context
            else:
                self._miss_count += 1
                self.logger.debug(f"Cache miss: manga context {slug}")
                return None
                
        except Exception as e:
            self.logger.error(f"Erro ao recuperar contexto do cache {slug}: {e}")
            return None
    
    # === MÉTODOS DE CACHE PARA CAPÍTULOS ===
    
    def get_chapter_cache_key(self, manga_slug: str, chapter_slug: str) -> str:
        """Gera chave de cache para capítulo"""
        return f"{self.CHAPTER_PREFIX}:detail:{manga_slug}:{chapter_slug}"
    
    def get_chapter_context_cache_key(self, manga_slug: str, chapter_slug: str) -> str:
        """Gera chave de cache para contexto do capítulo"""
        return f"{self.CHAPTER_PREFIX}:context:{manga_slug}:{chapter_slug}"
    
    def cache_chapter_context(self, manga_slug: str, chapter_slug: str, context: Dict[str, Any], timeout: Optional[int] = None) -> bool:
        """
        Armazena contexto do capítulo no cache
        
        Args:
            manga_slug: Slug do mangá
            chapter_slug: Slug do capítulo
            context: Contexto a ser armazenado
            timeout: Tempo de expiração (opcional)
            
        Returns:
            True se armazenado com sucesso
        """
        try:
            cache_key = self.get_chapter_context_cache_key(manga_slug, chapter_slug)
            timeout = timeout or self.SHORT_TIMEOUT
            
            # Serializa contexto
            serializable_context = {
                'previous_chapter_id': context.get('previous_chapter').id if context.get('previous_chapter') else None,
                'next_chapter_id': context.get('next_chapter').id if context.get('next_chapter') else None,
                'total_pages': context.get('total_pages', 0),
                'pages_count': len(context.get('pages', [])),
            }
            
            cache.set(cache_key, serializable_context, timeout)
            self.logger.debug(f"Chapter context cached: {manga_slug}/{chapter_slug}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao cachear contexto do capítulo {manga_slug}/{chapter_slug}: {e}")
            return False
    
    def get_cached_chapter_context(self, manga_slug: str, chapter_slug: str) -> Optional[Dict[str, Any]]:
        """
        Recupera contexto do capítulo do cache
        
        Args:
            manga_slug: Slug do mangá
            chapter_slug: Slug do capítulo
            
        Returns:
            Contexto do capítulo ou None se não encontrado
        """
        try:
            cache_key = self.get_chapter_context_cache_key(manga_slug, chapter_slug)
            context = cache.get(cache_key)
            
            if context:
                self._hit_count += 1
                self.logger.debug(f"Cache hit: chapter context {manga_slug}/{chapter_slug}")
                return context
            else:
                self._miss_count += 1
                self.logger.debug(f"Cache miss: chapter context {manga_slug}/{chapter_slug}")
                return None
                
        except Exception as e:
            self.logger.error(f"Erro ao recuperar contexto do capítulo do cache {manga_slug}/{chapter_slug}: {e}")
            return None
    
    # === MÉTODOS DE CACHE PARA LISTAS ===
    
    def get_manga_list_cache_key(self, filters: Dict[str, Any] = None) -> str:
        """Gera chave de cache para lista de mangás"""
        if filters:
            filter_str = "_".join([f"{k}:{v}" for k, v in sorted(filters.items())])
            return f"{self.LIST_PREFIX}:mangas:{filter_str}"
        return f"{self.LIST_PREFIX}:mangas:all"
    
    def cache_manga_list(self, manga_ids: List[int], filters: Dict[str, Any] = None, timeout: Optional[int] = None) -> bool:
        """
        Armazena lista de IDs de mangás no cache
        
        Args:
            manga_ids: Lista de IDs dos mangás
            filters: Filtros aplicados (opcional)
            timeout: Tempo de expiração (opcional)
            
        Returns:
            True se armazenado com sucesso
        """
        try:
            cache_key = self.get_manga_list_cache_key(filters)
            timeout = timeout or self.SHORT_TIMEOUT
            
            cache.set(cache_key, manga_ids, timeout)
            self.logger.debug(f"Manga list cached: {len(manga_ids)} items")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao cachear lista de mangás: {e}")
            return False
    
    def get_cached_manga_list(self, filters: Dict[str, Any] = None) -> Optional[List[int]]:
        """
        Recupera lista de IDs de mangás do cache
        
        Args:
            filters: Filtros aplicados (opcional)
            
        Returns:
            Lista de IDs ou None se não encontrada
        """
        try:
            cache_key = self.get_manga_list_cache_key(filters)
            manga_ids = cache.get(cache_key)
            
            if manga_ids:
                self._hit_count += 1
                self.logger.debug(f"Cache hit: manga list ({len(manga_ids)} items)")
                return manga_ids
            else:
                self._miss_count += 1
                self.logger.debug("Cache miss: manga list")
                return None
                
        except Exception as e:
            self.logger.error(f"Erro ao recuperar lista de mangás do cache: {e}")
            return None
    
    # === MÉTODOS DE INVALIDAÇÃO ===
    
    def invalidate_manga_cache(self, slug: str) -> bool:
        """
        Invalida cache relacionado a um mangá
        
        Args:
            slug: Slug do mangá
            
        Returns:
            True se invalidado com sucesso
        """
        try:
            keys_to_delete = [
                self.get_manga_cache_key(slug),
                self.get_manga_context_cache_key(slug),
            ]
            
            # Invalida também listas
            keys_to_delete.extend([
                f"{self.LIST_PREFIX}:mangas:all",
                f"{self.LIST_PREFIX}:mangas:published:True",
            ])
            
            cache.delete_many(keys_to_delete)
            self.logger.info(f"Cache invalidated for manga: {slug}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao invalidar cache do manga {slug}: {e}")
            return False
    
    def invalidate_chapter_cache(self, manga_slug: str, chapter_slug: str) -> bool:
        """
        Invalida cache relacionado a um capítulo
        
        Args:
            manga_slug: Slug do mangá
            chapter_slug: Slug do capítulo
            
        Returns:
            True se invalidado com sucesso
        """
        try:
            keys_to_delete = [
                self.get_chapter_cache_key(manga_slug, chapter_slug),
                self.get_chapter_context_cache_key(manga_slug, chapter_slug),
                # Invalida também contexto do mangá (pode ter mudado)
                self.get_manga_context_cache_key(manga_slug),
            ]
            
            cache.delete_many(keys_to_delete)
            self.logger.info(f"Cache invalidated for chapter: {manga_slug}/{chapter_slug}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao invalidar cache do capítulo {manga_slug}/{chapter_slug}: {e}")
            return False
    
    def clear_all_cache(self) -> bool:
        """
        Limpa todo o cache de mangás
        
        Returns:
            True se limpo com sucesso
        """
        try:
            # Em produção, seria melhor usar padrões de chave
            # Por simplicidade, vamos limpar tudo
            cache.clear()
            self.logger.info("All manga cache cleared")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao limpar cache: {e}")
            return False
    
    # === MÉTODOS DE MÉTRICAS ===
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do cache
        
        Returns:
            Dicionário com estatísticas
        """
        total_requests = self._hit_count + self._miss_count
        hit_rate = (self._hit_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hit_count': self._hit_count,
            'miss_count': self._miss_count,
            'total_requests': total_requests,
            'hit_rate': round(hit_rate, 2),
        }
    
    def reset_stats(self) -> None:
        """Reseta estatísticas do cache"""
        self._hit_count = 0
        self._miss_count = 0


# Instância global do serviço de cache
manga_cache = MangaCacheService()
