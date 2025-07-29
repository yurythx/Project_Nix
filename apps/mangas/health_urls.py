"""
URLs para health checks e monitoramento básico
Endpoints simples para load balancers e sistemas de monitoramento
"""

from django.urls import path
from .api.monitoring_views import HealthCheckView, ReadinessCheckView, LivenessCheckView

app_name = 'health'

urlpatterns = [
    # Health check básico (sem autenticação)
    path('health/', HealthCheckView.as_view(), name='health'),
    
    # Readiness check (pronto para receber tráfego)
    path('ready/', ReadinessCheckView.as_view(), name='ready'),
    
    # Liveness check (sistema vivo)
    path('live/', LivenessCheckView.as_view(), name='live'),
]

"""
Endpoints de Health Check:

=== HEALTH CHECKS (Sem autenticação) ===
GET /health/     - Health check completo
GET /ready/      - Readiness check (pronto para tráfego)
GET /live/       - Liveness check (sistema vivo)

=== RESPOSTAS ===

Health Check:
{
    "status": "healthy|unhealthy|error",
    "timestamp": "2024-01-01T12:00:00Z"
}

Readiness Check:
{
    "ready": true|false,
    "database": "healthy|unhealthy",
    "cache": "healthy|slow|unhealthy",
    "timestamp": "2024-01-01T12:00:00Z"
}

Liveness Check:
{
    "alive": true,
    "timestamp": "2024-01-01T12:00:00Z"
}

=== STATUS CODES ===
200 - Sistema saudável/pronto/vivo
503 - Sistema não saudável/não pronto
500 - Erro interno

=== USO ===
- Load Balancers: GET /health/ ou /ready/
- Kubernetes: GET /live/ (liveness) e /ready/ (readiness)
- Monitoramento: GET /health/ para status completo
"""
