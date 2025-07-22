"""
Health check views para monitoramento do sistema
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from django.db import connection
from django.core.cache import cache
# import redis  # Comentado temporariamente
import time
import os

@never_cache
@require_http_methods(["GET"])
def health_check(request):
    """
    Endpoint de health check para monitoramento
    """
    health_status = {
        'status': 'healthy',
        'timestamp': time.time(),
        'checks': {}
    }
    
    # Verificar banco de dados
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        health_status['checks']['database'] = {'status': 'healthy'}
    except Exception as e:
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_status['status'] = 'unhealthy'
    
    # Verificar cache/Redis
    try:
        cache.set('health_check', 'ok', 30)
        result = cache.get('health_check')
        if result == 'ok':
            health_status['checks']['cache'] = {'status': 'healthy'}
        else:
            raise Exception("Cache test failed")
    except Exception as e:
        health_status['checks']['cache'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_status['status'] = 'unhealthy'
    
    # Verificar Celery (se disponível)
    try:
        from celery import current_app
        inspect = current_app.control.inspect()
        stats = inspect.stats()
        if stats:
            health_status['checks']['celery'] = {'status': 'healthy'}
        else:
            health_status['checks']['celery'] = {
                'status': 'unhealthy',
                'error': 'No workers available'
            }
    except Exception as e:
        health_status['checks']['celery'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
    
    # Verificar espaço em disco
    try:
        statvfs = os.statvfs('/')
        free_space = statvfs.f_frsize * statvfs.f_bavail
        total_space = statvfs.f_frsize * statvfs.f_blocks
        usage_percent = ((total_space - free_space) / total_space) * 100
        
        if usage_percent < 90:
            health_status['checks']['disk'] = {
                'status': 'healthy',
                'usage_percent': round(usage_percent, 2)
            }
        else:
            health_status['checks']['disk'] = {
                'status': 'warning',
                'usage_percent': round(usage_percent, 2),
                'message': 'Disk usage high'
            }
    except Exception as e:
        health_status['checks']['disk'] = {
            'status': 'unknown',
            'error': str(e)
        }
    
    # Determinar status HTTP
    status_code = 200 if health_status['status'] == 'healthy' else 503
    
    return JsonResponse(health_status, status=status_code)

@never_cache
@require_http_methods(["GET"])
def readiness_check(request):
    """
    Endpoint de readiness check para Kubernetes
    """
    try:
        # Verificar se consegue conectar ao banco
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        return JsonResponse({'status': 'ready'}, status=200)
    except Exception as e:
        return JsonResponse({
            'status': 'not ready',
            'error': str(e)
        }, status=503)

@never_cache
@require_http_methods(["GET"])
def liveness_check(request):
    """
    Endpoint de liveness check para Kubernetes
    """
    return JsonResponse({'status': 'alive'}, status=200)
