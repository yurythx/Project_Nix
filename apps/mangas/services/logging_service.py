"""
Serviço de logging estruturado para mangás
Implementa logging centralizado com contexto e métricas
"""

import logging
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime
from django.conf import settings
from django.contrib.auth.models import User

from ..models.manga import Manga
from ..models.capitulo import Capitulo


class MangaLogger:
    """
    Logger estruturado para operações de mangás
    
    Funcionalidades:
    - Logging estruturado com contexto
    - Métricas de performance
    - Rastreamento de usuários
    - Correlação de eventos
    """
    
    def __init__(self, name: str = __name__):
        self.logger = logging.getLogger(name)
        self.start_time = None
        self.context = {}
    
    def set_context(self, **kwargs):
        """Define contexto para logs subsequentes"""
        self.context.update(kwargs)
    
    def clear_context(self):
        """Limpa contexto atual"""
        self.context = {}
    
    def start_timer(self):
        """Inicia timer para métricas de performance"""
        self.start_time = time.time()
    
    def get_duration(self) -> Optional[float]:
        """Retorna duração desde start_timer()"""
        if self.start_time:
            return round(time.time() - self.start_time, 3)
        return None
    
    def _build_log_data(self, message: str, **kwargs) -> Dict[str, Any]:
        """Constrói dados estruturados do log"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'message': message,
            'context': self.context.copy(),
            **kwargs
        }
        
        # Adiciona duração se timer foi iniciado
        duration = self.get_duration()
        if duration is not None:
            log_data['duration_seconds'] = duration
        
        return log_data
    
    def info(self, message: str, **kwargs):
        """Log de informação estruturado"""
        log_data = self._build_log_data(message, **kwargs)
        self.logger.info(json.dumps(log_data))
    
    def warning(self, message: str, **kwargs):
        """Log de warning estruturado"""
        log_data = self._build_log_data(message, **kwargs)
        self.logger.warning(json.dumps(log_data))
    
    def error(self, message: str, error: Exception = None, **kwargs):
        """Log de erro estruturado"""
        log_data = self._build_log_data(message, **kwargs)
        
        if error:
            log_data['error'] = {
                'type': type(error).__name__,
                'message': str(error),
            }
        
        self.logger.error(json.dumps(log_data))
    
    def debug(self, message: str, **kwargs):
        """Log de debug estruturado"""
        log_data = self._build_log_data(message, **kwargs)
        self.logger.debug(json.dumps(log_data))
    
    # === MÉTODOS ESPECÍFICOS PARA MANGÁS ===
    
    def log_manga_view(self, manga: Manga, user: Optional[User] = None, request_ip: str = None):
        """Log de visualização de mangá"""
        self.info(
            "Manga viewed",
            manga_id=manga.id,
            manga_slug=manga.slug,
            manga_title=manga.title,
            user_id=user.id if user else None,
            user_username=user.username if user else None,
            request_ip=request_ip,
            view_count=manga.view_count,
            event_type="manga_view"
        )
    
    def log_chapter_view(self, chapter: Capitulo, user: Optional[User] = None, request_ip: str = None):
        """Log de visualização de capítulo"""
        self.info(
            "Chapter viewed",
            chapter_id=chapter.id,
            chapter_slug=chapter.slug,
            chapter_title=chapter.title,
            chapter_number=chapter.number,
            manga_id=chapter.volume.manga.id,
            manga_slug=chapter.volume.manga.slug,
            volume_id=chapter.volume.id,
            volume_number=chapter.volume.number,
            user_id=user.id if user else None,
            user_username=user.username if user else None,
            request_ip=request_ip,
            event_type="chapter_view"
        )
    
    def log_manga_search(self, query: str, results_count: int, user: Optional[User] = None):
        """Log de busca de mangás"""
        self.info(
            "Manga search performed",
            search_query=query,
            results_count=results_count,
            user_id=user.id if user else None,
            user_username=user.username if user else None,
            event_type="manga_search"
        )
    
    def log_manga_creation(self, manga: Manga, user: User):
        """Log de criação de mangá"""
        self.info(
            "Manga created",
            manga_id=manga.id,
            manga_slug=manga.slug,
            manga_title=manga.title,
            manga_author=manga.author,
            created_by_id=user.id,
            created_by_username=user.username,
            event_type="manga_creation"
        )
    
    def log_manga_update(self, manga: Manga, user: User, updated_fields: list = None):
        """Log de atualização de mangá"""
        self.info(
            "Manga updated",
            manga_id=manga.id,
            manga_slug=manga.slug,
            manga_title=manga.title,
            updated_by_id=user.id,
            updated_by_username=user.username,
            updated_fields=updated_fields or [],
            event_type="manga_update"
        )
    
    def log_manga_deletion(self, manga: Manga, user: User):
        """Log de exclusão de mangá"""
        self.warning(
            "Manga deleted",
            manga_id=manga.id,
            manga_slug=manga.slug,
            manga_title=manga.title,
            deleted_by_id=user.id,
            deleted_by_username=user.username,
            event_type="manga_deletion"
        )
    
    def log_cache_operation(self, operation: str, cache_key: str, hit: bool = None, duration: float = None):
        """Log de operações de cache"""
        log_data = {
            'cache_operation': operation,
            'cache_key': cache_key,
            'event_type': 'cache_operation'
        }
        
        if hit is not None:
            log_data['cache_hit'] = hit
        
        if duration is not None:
            log_data['cache_duration_ms'] = round(duration * 1000, 2)
        
        self.debug(f"Cache {operation}", **log_data)
    
    def log_api_request(self, endpoint: str, method: str, user: Optional[User] = None, 
                       status_code: int = None, response_time: float = None):
        """Log de requisições da API"""
        log_data = {
            'api_endpoint': endpoint,
            'http_method': method,
            'user_id': user.id if user else None,
            'user_username': user.username if user else None,
            'event_type': 'api_request'
        }
        
        if status_code is not None:
            log_data['status_code'] = status_code
        
        if response_time is not None:
            log_data['response_time_ms'] = round(response_time * 1000, 2)
        
        self.info(f"API {method} {endpoint}", **log_data)
    
    def log_performance_metric(self, operation: str, duration: float, **kwargs):
        """Log de métricas de performance"""
        self.info(
            f"Performance metric: {operation}",
            operation=operation,
            duration_seconds=duration,
            duration_ms=round(duration * 1000, 2),
            event_type="performance_metric",
            **kwargs
        )
    
    def log_error_with_context(self, error: Exception, operation: str, **kwargs):
        """Log de erro com contexto completo"""
        self.error(
            f"Error in {operation}",
            error=error,
            operation=operation,
            event_type="error",
            **kwargs
        )


class MangaLoggerMiddleware:
    """
    Middleware para logging automático de requisições
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = MangaLogger('manga_middleware')
    
    def __call__(self, request):
        # Inicia timer
        start_time = time.time()
        
        # Processa requisição
        response = self.get_response(request)
        
        # Calcula tempo de resposta
        response_time = time.time() - start_time
        
        # Log apenas para endpoints de mangás
        if '/mangas/' in request.path or '/api/mangas/' in request.path:
            self.logger.log_api_request(
                endpoint=request.path,
                method=request.method,
                user=request.user if request.user.is_authenticated else None,
                status_code=response.status_code,
                response_time=response_time
            )
        
        return response


# Instâncias globais para uso direto
manga_logger = MangaLogger('manga_service')
api_logger = MangaLogger('manga_api')
cache_logger = MangaLogger('manga_cache')


# Decorador para logging automático de performance
def log_performance(operation_name: str = None):
    """
    Decorador para logging automático de performance
    
    Usage:
        @log_performance("get_manga_by_slug")
        def get_manga_by_slug(self, slug):
            # código da função
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = MangaLogger(func.__module__)
            operation = operation_name or f"{func.__name__}"
            
            logger.start_timer()
            try:
                result = func(*args, **kwargs)
                duration = logger.get_duration()
                logger.log_performance_metric(operation, duration)
                return result
            except Exception as e:
                duration = logger.get_duration()
                logger.log_error_with_context(e, operation, duration_seconds=duration)
                raise
        
        return wrapper
    return decorator
