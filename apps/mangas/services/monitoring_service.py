"""
Serviço de monitoramento e métricas para mangás
Implementa coleta e análise de métricas de performance e uso
"""

import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from django.core.cache import cache
from django.db.models import Count, Avg, Max, Min
from django.contrib.auth.models import User

from ..models.manga import Manga
from ..models.capitulo import Capitulo
from ..models.pagina import Pagina
from ..services.cache_service import manga_cache
from ..services.logging_service import manga_logger


class MangaMonitoringService:
    """
    Serviço de monitoramento para mangás
    
    Funcionalidades:
    - Métricas de performance
    - Estatísticas de uso
    - Health checks
    - Alertas automáticos
    """
    
    def __init__(self):
        self.logger = manga_logger
        self.cache_prefix = "monitoring"
    
    # === MÉTRICAS DE PERFORMANCE ===
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Retorna métricas de performance do sistema
        
        Returns:
            Dicionário com métricas de performance
        """
        try:
            # Cache das métricas por 5 minutos
            cache_key = f"{self.cache_prefix}:performance"
            cached_metrics = cache.get(cache_key)
            
            if cached_metrics:
                return cached_metrics
            
            # Coleta métricas do banco
            start_time = time.time()
            
            metrics = {
                'database': self._get_database_metrics(),
                'cache': self._get_cache_metrics(),
                'content': self._get_content_metrics(),
                'users': self._get_user_metrics(),
                'timestamp': datetime.utcnow().isoformat(),
            }
            
            # Tempo de coleta das métricas
            collection_time = time.time() - start_time
            metrics['collection_time_seconds'] = round(collection_time, 3)
            
            # Cache por 5 minutos
            cache.set(cache_key, metrics, 300)
            
            self.logger.log_performance_metric(
                "metrics_collection",
                collection_time,
                metrics_count=len(metrics)
            )
            
            return metrics
            
        except Exception as e:
            self.logger.log_error_with_context(e, "get_performance_metrics")
            return {'error': str(e)}
    
    def _get_database_metrics(self) -> Dict[str, Any]:
        """Coleta métricas do banco de dados"""
        return {
            'total_mangas': Manga.objects.count(),
            'published_mangas': Manga.objects.filter(is_published=True).count(),
            'total_chapters': Capitulo.objects.count(),
            'published_chapters': Capitulo.objects.filter(is_published=True).count(),
            'total_pages': Pagina.objects.count(),
            'total_users': User.objects.count(),
            'active_users_30d': User.objects.filter(
                last_login__gte=datetime.now() - timedelta(days=30)
            ).count(),
        }
    
    def _get_cache_metrics(self) -> Dict[str, Any]:
        """Coleta métricas do cache"""
        cache_stats = manga_cache.get_cache_stats()
        return {
            'hit_rate': cache_stats.get('hit_rate', 0),
            'total_requests': cache_stats.get('total_requests', 0),
            'hit_count': cache_stats.get('hit_count', 0),
            'miss_count': cache_stats.get('miss_count', 0),
        }
    
    def _get_content_metrics(self) -> Dict[str, Any]:
        """Coleta métricas de conteúdo"""
        # Mangás mais visualizados
        top_mangas = Manga.objects.filter(is_published=True).order_by('-view_count')[:5]
        
        # Estatísticas de visualizações
        view_stats = Manga.objects.filter(is_published=True).aggregate(
            avg_views=Avg('view_count'),
            max_views=Max('view_count'),
            min_views=Min('view_count'),
            total_views=Count('view_count')
        )
        
        return {
            'top_mangas': [
                {
                    'slug': manga.slug,
                    'title': manga.title,
                    'view_count': manga.view_count
                }
                for manga in top_mangas
            ],
            'view_statistics': view_stats,
            'avg_chapters_per_manga': self._get_avg_chapters_per_manga(),
            'avg_pages_per_chapter': self._get_avg_pages_per_chapter(),
        }
    
    def _get_user_metrics(self) -> Dict[str, Any]:
        """Coleta métricas de usuários"""
        return {
            'total_users': User.objects.count(),
            'active_users_7d': User.objects.filter(
                last_login__gte=datetime.now() - timedelta(days=7)
            ).count(),
            'active_users_30d': User.objects.filter(
                last_login__gte=datetime.now() - timedelta(days=30)
            ).count(),
            'staff_users': User.objects.filter(is_staff=True).count(),
            'superusers': User.objects.filter(is_superuser=True).count(),
        }
    
    def _get_avg_chapters_per_manga(self) -> float:
        """Calcula média de capítulos por mangá"""
        try:
            mangas_with_chapters = Manga.objects.filter(
                is_published=True,
                volumes__capitulos__isnull=False
            ).annotate(
                chapter_count=Count('volumes__capitulos')
            ).aggregate(
                avg_chapters=Avg('chapter_count')
            )
            return round(mangas_with_chapters.get('avg_chapters', 0), 2)
        except:
            return 0.0
    
    def _get_avg_pages_per_chapter(self) -> float:
        """Calcula média de páginas por capítulo"""
        try:
            chapters_with_pages = Capitulo.objects.filter(
                is_published=True,
                paginas__isnull=False
            ).annotate(
                page_count=Count('paginas')
            ).aggregate(
                avg_pages=Avg('page_count')
            )
            return round(chapters_with_pages.get('avg_pages', 0), 2)
        except:
            return 0.0
    
    # === HEALTH CHECKS ===
    
    def health_check(self) -> Dict[str, Any]:
        """
        Executa health check completo do sistema
        
        Returns:
            Status de saúde do sistema
        """
        try:
            start_time = time.time()
            
            health_status = {
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'checks': {}
            }
            
            # Check do banco de dados
            health_status['checks']['database'] = self._check_database()
            
            # Check do cache
            health_status['checks']['cache'] = self._check_cache()
            
            # Check de conteúdo
            health_status['checks']['content'] = self._check_content()
            
            # Determina status geral
            failed_checks = [
                check for check in health_status['checks'].values()
                if check['status'] != 'healthy'
            ]
            
            if failed_checks:
                health_status['status'] = 'unhealthy'
                health_status['failed_checks'] = len(failed_checks)
            
            # Tempo total do health check
            health_status['check_duration_seconds'] = round(time.time() - start_time, 3)
            
            return health_status
            
        except Exception as e:
            self.logger.log_error_with_context(e, "health_check")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _check_database(self) -> Dict[str, Any]:
        """Verifica saúde do banco de dados"""
        try:
            start_time = time.time()
            
            # Testa consulta simples
            manga_count = Manga.objects.count()
            
            duration = time.time() - start_time
            
            if duration > 1.0:  # Mais de 1 segundo é lento
                return {
                    'status': 'slow',
                    'duration_seconds': round(duration, 3),
                    'manga_count': manga_count,
                    'message': 'Database responding slowly'
                }
            
            return {
                'status': 'healthy',
                'duration_seconds': round(duration, 3),
                'manga_count': manga_count
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def _check_cache(self) -> Dict[str, Any]:
        """Verifica saúde do cache"""
        try:
            start_time = time.time()
            
            # Testa operação de cache
            test_key = f"{self.cache_prefix}:health_check"
            test_value = {'test': True, 'timestamp': time.time()}
            
            cache.set(test_key, test_value, 60)
            retrieved_value = cache.get(test_key)
            
            duration = time.time() - start_time
            
            if retrieved_value != test_value:
                return {
                    'status': 'unhealthy',
                    'error': 'Cache read/write test failed'
                }
            
            # Limpa teste
            cache.delete(test_key)
            
            return {
                'status': 'healthy',
                'duration_seconds': round(duration, 3)
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def _check_content(self) -> Dict[str, Any]:
        """Verifica integridade do conteúdo"""
        try:
            # Verifica se há mangás órfãos (sem volumes)
            orphaned_mangas = Manga.objects.filter(
                is_published=True,
                volumes__isnull=True
            ).count()
            
            # Verifica capítulos órfãos (sem páginas)
            orphaned_chapters = Capitulo.objects.filter(
                is_published=True,
                paginas__isnull=True
            ).count()
            
            issues = []
            if orphaned_mangas > 0:
                issues.append(f"{orphaned_mangas} mangás sem volumes")
            
            if orphaned_chapters > 0:
                issues.append(f"{orphaned_chapters} capítulos sem páginas")
            
            if issues:
                return {
                    'status': 'warning',
                    'issues': issues,
                    'orphaned_mangas': orphaned_mangas,
                    'orphaned_chapters': orphaned_chapters
                }
            
            return {
                'status': 'healthy',
                'orphaned_mangas': 0,
                'orphaned_chapters': 0
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    # === ALERTAS ===
    
    def check_alerts(self) -> List[Dict[str, Any]]:
        """
        Verifica condições de alerta
        
        Returns:
            Lista de alertas ativos
        """
        alerts = []
        
        try:
            # Alerta de performance
            performance_metrics = self.get_performance_metrics()
            cache_hit_rate = performance_metrics.get('cache', {}).get('hit_rate', 0)
            
            if cache_hit_rate < 70:  # Hit rate abaixo de 70%
                alerts.append({
                    'type': 'performance',
                    'severity': 'warning',
                    'message': f'Cache hit rate baixo: {cache_hit_rate}%',
                    'metric': 'cache_hit_rate',
                    'value': cache_hit_rate,
                    'threshold': 70
                })
            
            # Alerta de conteúdo
            health = self.health_check()
            content_check = health.get('checks', {}).get('content', {})
            
            if content_check.get('status') == 'warning':
                alerts.append({
                    'type': 'content',
                    'severity': 'warning',
                    'message': 'Problemas de integridade de conteúdo detectados',
                    'issues': content_check.get('issues', [])
                })
            
            return alerts
            
        except Exception as e:
            self.logger.log_error_with_context(e, "check_alerts")
            return [{
                'type': 'system',
                'severity': 'error',
                'message': f'Erro ao verificar alertas: {str(e)}'
            }]


# Instância global do serviço de monitoramento
manga_monitoring = MangaMonitoringService()
