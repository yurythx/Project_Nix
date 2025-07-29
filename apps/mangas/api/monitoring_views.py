"""
Views para monitoramento e métricas da API
Endpoints para health checks e métricas de performance
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.http import JsonResponse
from django.views import View

from ..services.monitoring_service import manga_monitoring
from ..services.cache_service import manga_cache
from ..services.logging_service import api_logger


class MonitoringViewSet(viewsets.ViewSet):
    """
    ViewSet para endpoints de monitoramento
    
    Endpoints disponíveis:
    - GET /api/monitoring/health/ - Health check
    - GET /api/monitoring/metrics/ - Métricas de performance
    - GET /api/monitoring/alerts/ - Alertas ativos
    """
    
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """
        Lista endpoints de monitoramento disponíveis
        
        GET /api/monitoring/
        """
        endpoints = {
            'health': '/api/monitoring/health/',
            'metrics': '/api/monitoring/metrics/',
            'alerts': '/api/monitoring/alerts/',
            'cache_stats': '/api/monitoring/cache/',
        }
        
        return Response({
            'message': 'Manga Monitoring API',
            'endpoints': endpoints,
            'user': request.user.username,
            'permissions': {
                'is_staff': request.user.is_staff,
                'is_superuser': request.user.is_superuser,
            }
        })
    
    @action(detail=False, methods=['get'])
    def health(self, request):
        """
        Health check do sistema
        
        GET /api/monitoring/health/
        """
        try:
            health_status = manga_monitoring.health_check()
            
            # Log do health check
            api_logger.info(
                "Health check performed",
                status=health_status.get('status'),
                user_id=request.user.id,
                failed_checks=health_status.get('failed_checks', 0)
            )
            
            # Status HTTP baseado na saúde
            http_status = status.HTTP_200_OK
            if health_status.get('status') == 'unhealthy':
                http_status = status.HTTP_503_SERVICE_UNAVAILABLE
            elif health_status.get('status') == 'error':
                http_status = status.HTTP_500_INTERNAL_SERVER_ERROR
            
            return Response(health_status, status=http_status)
            
        except Exception as e:
            api_logger.error(
                "Health check failed",
                error=e,
                user_id=request.user.id
            )
            return Response(
                {'error': 'Health check failed', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def metrics(self, request):
        """
        Métricas de performance do sistema
        
        GET /api/monitoring/metrics/
        """
        # Apenas staff pode ver métricas detalhadas
        if not request.user.is_staff:
            return Response(
                {'error': 'Acesso negado. Apenas staff pode ver métricas.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            metrics = manga_monitoring.get_performance_metrics()
            
            # Log da consulta de métricas
            api_logger.info(
                "Metrics accessed",
                user_id=request.user.id,
                metrics_count=len(metrics)
            )
            
            return Response(metrics)
            
        except Exception as e:
            api_logger.error(
                "Metrics access failed",
                error=e,
                user_id=request.user.id
            )
            return Response(
                {'error': 'Failed to get metrics', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def alerts(self, request):
        """
        Alertas ativos do sistema
        
        GET /api/monitoring/alerts/
        """
        # Apenas staff pode ver alertas
        if not request.user.is_staff:
            return Response(
                {'error': 'Acesso negado. Apenas staff pode ver alertas.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            alerts = manga_monitoring.check_alerts()
            
            # Log da consulta de alertas
            api_logger.info(
                "Alerts checked",
                user_id=request.user.id,
                alerts_count=len(alerts)
            )
            
            return Response({
                'alerts': alerts,
                'count': len(alerts),
                'has_critical': any(alert.get('severity') == 'error' for alert in alerts),
                'has_warnings': any(alert.get('severity') == 'warning' for alert in alerts),
            })
            
        except Exception as e:
            api_logger.error(
                "Alerts check failed",
                error=e,
                user_id=request.user.id
            )
            return Response(
                {'error': 'Failed to check alerts', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def cache(self, request):
        """
        Estatísticas do cache
        
        GET /api/monitoring/cache/
        """
        try:
            cache_stats = manga_cache.get_cache_stats()
            
            # Log da consulta de cache
            api_logger.info(
                "Cache stats accessed",
                user_id=request.user.id,
                hit_rate=cache_stats.get('hit_rate', 0)
            )
            
            return Response(cache_stats)
            
        except Exception as e:
            api_logger.error(
                "Cache stats access failed",
                error=e,
                user_id=request.user.id
            )
            return Response(
                {'error': 'Failed to get cache stats', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class HealthCheckView(View):
    """
    View simples para health check (sem autenticação)
    Para uso por load balancers e sistemas de monitoramento
    """
    
    def get(self, request):
        """
        Health check básico
        
        GET /health/
        """
        try:
            # Health check simplificado
            health_status = manga_monitoring.health_check()
            
            # Resposta JSON simples
            response_data = {
                'status': health_status.get('status', 'unknown'),
                'timestamp': health_status.get('timestamp'),
            }
            
            # Status HTTP baseado na saúde
            http_status = 200
            if health_status.get('status') == 'unhealthy':
                http_status = 503
            elif health_status.get('status') == 'error':
                http_status = 500
            
            return JsonResponse(response_data, status=http_status)
            
        except Exception as e:
            return JsonResponse(
                {'status': 'error', 'message': str(e)},
                status=500
            )


class ReadinessCheckView(View):
    """
    View para readiness check
    Verifica se o sistema está pronto para receber tráfego
    """
    
    def get(self, request):
        """
        Readiness check
        
        GET /ready/
        """
        try:
            # Verifica componentes críticos
            health_status = manga_monitoring.health_check()
            
            # Sistema está pronto se database e cache estão funcionais
            db_status = health_status.get('checks', {}).get('database', {}).get('status')
            cache_status = health_status.get('checks', {}).get('cache', {}).get('status')
            
            is_ready = db_status == 'healthy' and cache_status in ['healthy', 'slow']
            
            response_data = {
                'ready': is_ready,
                'database': db_status,
                'cache': cache_status,
                'timestamp': health_status.get('timestamp'),
            }
            
            http_status = 200 if is_ready else 503
            
            return JsonResponse(response_data, status=http_status)
            
        except Exception as e:
            return JsonResponse(
                {'ready': False, 'error': str(e)},
                status=500
            )


class LivenessCheckView(View):
    """
    View para liveness check
    Verifica se o sistema está vivo (não travado)
    """
    
    def get(self, request):
        """
        Liveness check
        
        GET /live/
        """
        # Liveness check muito simples - apenas responde
        return JsonResponse({
            'alive': True,
            'timestamp': manga_monitoring.health_check().get('timestamp')
        })
