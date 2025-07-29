"""
Configuração do Celery para tarefas em background.
"""

import os
from celery import Celery
from django.conf import settings

# Definir o módulo de configurações padrão do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Criar instância do Celery
app = Celery('project_nix')

# Usar configurações do Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-descobrir tarefas em todos os apps registrados
app.autodiscover_tasks()

# Configurações específicas do Celery
app.conf.update(
    # Broker (Redis recomendado para produção)
    broker_url=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    result_backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    
    # Configurações de tarefas
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Sao_Paulo',
    enable_utc=True,
    
    # Configurações de workers
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Configurações de filas
    task_default_queue='default',
    task_queues={
        'default': {
            'exchange': 'default',
            'routing_key': 'default',
        },
        'downloads': {
            'exchange': 'downloads',
            'routing_key': 'downloads',
        },
        'notifications': {
            'exchange': 'notifications',
            'routing_key': 'notifications',
        },
        'moderation': {
            'exchange': 'moderation',
            'routing_key': 'moderation',
        },
        'batch_downloads': {
            'exchange': 'batch_downloads',
            'routing_key': 'batch_downloads',
        },
    },
    
    # Configurações de roteamento
    task_routes={
        'apps.mangas.tasks.download_tasks.*': {'queue': 'downloads'},
        'apps.mangas.tasks.notification_tasks.*': {'queue': 'notifications'},
        'apps.mangas.tasks.moderation_tasks.*': {'queue': 'moderation'},
        'apps.mangas.tasks.batch_download_tasks.*': {'queue': 'batch_downloads'},
    },
    
    # Configurações de beat (tarefas periódicas)
    beat_schedule={
        'cleanup-expired-downloads': {
            'task': 'apps.mangas.tasks.download_tasks.cleanup_expired_downloads',
            'schedule': 3600.0,  # A cada hora
        },
        'cleanup-expired-notifications': {
            'task': 'apps.mangas.tasks.notification_tasks.cleanup_expired_notifications',
            'schedule': 3600.0,  # A cada hora
        },
        'process-moderation-queue': {
            'task': 'apps.mangas.tasks.moderation_tasks.process_moderation_queue',
            'schedule': 300.0,  # A cada 5 minutos
        },
        'send-pending-notifications': {
            'task': 'apps.mangas.tasks.notification_tasks.send_pending_notifications',
            'schedule': 60.0,  # A cada minuto
        },
        # Novas tasks para mangás
        'update-manga-statistics': {
            'task': 'apps.mangas.tasks.manga_tasks.update_manga_statistics',
            'schedule': 1800.0,  # A cada 30 minutos
        },
        'cleanup-manga-cache': {
            'task': 'apps.mangas.tasks.manga_tasks.cleanup_manga_cache',
            'schedule': 7200.0,  # A cada 2 horas
        },
    },
    
    # Configurações de retry
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_always_eager=False,  # False para produção
    
    # Configurações de logging
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
)

@app.task(bind=True)
def debug_task(self):
    """Tarefa de debug para testar o Celery."""
    print(f'Request: {self.request!r}')
    return 'Celery está funcionando!'

# Configurações específicas para desenvolvimento
if settings.DEBUG:
    app.conf.update(
        task_always_eager=True,  # Executar tarefas sincronamente em desenvolvimento
        task_eager_propagates=True,
    ) 