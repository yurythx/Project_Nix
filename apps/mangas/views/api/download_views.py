"""
Views API para o sistema de downloads offline.
"""

import json
from typing import Dict, Any
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View

from ...models.capitulo import Capitulo
from ...models.offline_download import OfflineDownload, DownloadPreferences
from ...models.batch_download import BatchDownload, BatchDownloadTemplate
from ...services.download_service import DownloadService
from ...services.batch_download_service import BatchDownloadService

download_service = DownloadService()
batch_download_service = BatchDownloadService()

class DownloadAPIView(View):
    """
    View base para APIs de download.
    """
    
    def dispatch(self, request, *args, **kwargs):
        """Adiciona CSRF exemption para APIs."""
        return super().dispatch(request, *args, **kwargs)

@method_decorator(csrf_exempt, name='dispatch')
class ChapterDownloadView(DownloadAPIView):
    """
    API para downloads de capítulos individuais.
    """
    
    def post(self, request: HttpRequest, chapter_id: int) -> JsonResponse:
        """Inicia download de um capítulo."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Usuário não autenticado'}, status=401)
        
        try:
            capitulo = Capitulo.objects.get(id=chapter_id, is_published=True)
        except Capitulo.DoesNotExist:
            return JsonResponse({'error': 'Capítulo não encontrado'}, status=404)
        
        try:
            # Criar download
            download = download_service.create_download(request.user, capitulo)
            
            return JsonResponse({
                'success': True,
                'download': {
                    'id': download.id,
                    'status': download.status,
                    'progress': download.download_progress,
                    'capitulo': {
                        'id': capitulo.id,
                        'number': capitulo.number,
                        'title': capitulo.title,
                        'manga': {
                            'id': capitulo.manga.id,
                            'title': capitulo.manga.title,
                        }
                    }
                }
            })
            
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'error': 'Erro interno do servidor'}, status=500)
    
    def get(self, request: HttpRequest, chapter_id: int) -> JsonResponse:
        """Obtém status de downloads de um capítulo."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Usuário não autenticado'}, status=401)
        
        try:
            capitulo = Capitulo.objects.get(id=chapter_id)
        except Capitulo.DoesNotExist:
            return JsonResponse({'error': 'Capítulo não encontrado'}, status=404)
        
        # Obter downloads do usuário para este capítulo
        downloads = OfflineDownload.objects.filter(
            user=request.user,
            capitulo=capitulo
        ).order_by('-created_at')
        
        download_list = []
        for download in downloads:
            download_data = {
                'id': download.id,
                'status': download.status,
                'progress': download.download_progress,
                'file_size': download.file_size,
                'created_at': download.created_at.isoformat(),
                'completed_at': download.completed_at.isoformat() if download.completed_at else None,
                'expires_at': download.expires_at.isoformat() if download.expires_at else None,
                'is_available': download.is_available,
                'download_url': download.get_file_url(),
            }
            download_list.append(download_data)
        
        return JsonResponse({
            'downloads': download_list
        })

@method_decorator(csrf_exempt, name='dispatch')
class DownloadStatusView(DownloadAPIView):
    """
    API para status de downloads.
    """
    
    def get(self, request: HttpRequest, download_id: int) -> JsonResponse:
        """Obtém status detalhado de um download."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Usuário não autenticado'}, status=401)
        
        try:
            status = download_service.get_download_status(download_id, request.user)
            return JsonResponse({'status': status})
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=404)
        except Exception as e:
            return JsonResponse({'error': 'Erro interno do servidor'}, status=500)
    
    def delete(self, request: HttpRequest, download_id: int) -> JsonResponse:
        """Remove um download."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Usuário não autenticado'}, status=401)
        
        try:
            success = download_service.delete_download(download_id, request.user)
            return JsonResponse({'success': success})
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=404)
        except Exception as e:
            return JsonResponse({'error': 'Erro interno do servidor'}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class UserDownloadsView(DownloadAPIView):
    """
    API para downloads do usuário.
    """
    
    def get(self, request: HttpRequest) -> JsonResponse:
        """Obtém todos os downloads do usuário."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Usuário não autenticado'}, status=401)
        
        status_filter = request.GET.get('status')
        downloads = download_service.get_user_downloads(request.user, status_filter)
        
        download_list = []
        for download in downloads:
            download_data = {
                'id': download.id,
                'status': download.status,
                'progress': download.download_progress,
                'file_size': download.file_size,
                'created_at': download.created_at.isoformat(),
                'completed_at': download.completed_at.isoformat() if download.completed_at else None,
                'expires_at': download.expires_at.isoformat() if download.expires_at else None,
                'is_available': download.is_available,
                'download_url': download.get_file_url(),
                'capitulo': {
                    'id': download.capitulo.id,
                    'number': download.capitulo.number,
                    'title': download.capitulo.title,
                    'manga': {
                        'id': download.capitulo.manga.id,
                        'title': download.capitulo.manga.title,
                    }
                }
            }
            download_list.append(download_data)
        
        return JsonResponse({
            'downloads': download_list
        })

@method_decorator(csrf_exempt, name='dispatch')
class DownloadStatsView(DownloadAPIView):
    """
    API para estatísticas de downloads.
    """
    
    def get(self, request: HttpRequest) -> JsonResponse:
        """Obtém estatísticas de downloads do usuário."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Usuário não autenticado'}, status=401)
        
        stats = download_service.get_download_stats(request.user)
        queue_status = download_service.get_download_queue_status(request.user)
        
        return JsonResponse({
            'stats': stats,
            'queue_status': queue_status
        })

@method_decorator(csrf_exempt, name='dispatch')
class DownloadPreferencesView(DownloadAPIView):
    """
    API para preferências de download.
    """
    
    def get(self, request: HttpRequest) -> JsonResponse:
        """Obtém preferências de download do usuário."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Usuário não autenticado'}, status=401)
        
        preferences, created = DownloadPreferences.objects.get_or_create(
            user=request.user,
            defaults={
                'max_storage_size': 1024,
                'keep_downloads_for_days': 30,
                'notify_on_completion': True,
            }
        )
        
        return JsonResponse({
            'preferences': {
                'auto_download_new_chapters': preferences.auto_download_new_chapters,
                'download_quality': preferences.download_quality,
                'max_storage_size': preferences.max_storage_size,
                'download_location': preferences.download_location,
                'keep_downloads_for_days': preferences.keep_downloads_for_days,
                'notify_on_completion': preferences.notify_on_completion,
                'current_storage_usage': preferences.current_storage_usage,
                'storage_usage_percentage': preferences.storage_usage_percentage,
            }
        })
    
    def put(self, request: HttpRequest) -> JsonResponse:
        """Atualiza preferências de download do usuário."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Usuário não autenticado'}, status=401)
        
        try:
            data = json.loads(request.body)
            preferences, created = DownloadPreferences.objects.get_or_create(
                user=request.user,
                defaults={
                    'max_storage_size': 1024,
                    'keep_downloads_for_days': 30,
                    'notify_on_completion': True,
                }
            )
            
            # Atualizar campos
            if 'auto_download_new_chapters' in data:
                preferences.auto_download_new_chapters = data['auto_download_new_chapters']
            if 'download_quality' in data:
                preferences.download_quality = data['download_quality']
            if 'max_storage_size' in data:
                preferences.max_storage_size = data['max_storage_size']
            if 'download_location' in data:
                preferences.download_location = data['download_location']
            if 'keep_downloads_for_days' in data:
                preferences.keep_downloads_for_days = data['keep_downloads_for_days']
            if 'notify_on_completion' in data:
                preferences.notify_on_completion = data['notify_on_completion']
            
            preferences.save()
            
            return JsonResponse({
                'success': True,
                'preferences': {
                    'auto_download_new_chapters': preferences.auto_download_new_chapters,
                    'download_quality': preferences.download_quality,
                    'max_storage_size': preferences.max_storage_size,
                    'download_location': preferences.download_location,
                    'keep_downloads_for_days': preferences.keep_downloads_for_days,
                    'notify_on_completion': preferences.notify_on_completion,
                    'current_storage_usage': preferences.current_storage_usage,
                    'storage_usage_percentage': preferences.storage_usage_percentage,
                }
            })
            
        except Exception as e:
            return JsonResponse({'error': 'Erro interno do servidor'}, status=500)

# Batch Download APIs

@method_decorator(csrf_exempt, name='dispatch')
class BatchDownloadView(DownloadAPIView):
    """
    API para downloads em lote.
    """
    
    def post(self, request: HttpRequest) -> JsonResponse:
        """Cria um novo download em lote."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Usuário não autenticado'}, status=401)
        
        try:
            data = json.loads(request.body)
            manga_id = data.get('manga_id')
            name = data.get('name', '').strip()
            start_chapter = data.get('start_chapter')
            end_chapter = data.get('end_chapter')
            volume_filter = data.get('volume_filter', '').strip()
            quality = data.get('quality', 'original')
            template_id = data.get('template_id')
            
            if not manga_id:
                return JsonResponse({'error': 'ID do mangá é obrigatório'}, status=400)
            if not name:
                return JsonResponse({'error': 'Nome do lote é obrigatório'}, status=400)
            
            # Criar download em lote
            batch_download = batch_download_service.create_batch_download(
                user=request.user,
                manga_id=manga_id,
                name=name,
                start_chapter=start_chapter,
                end_chapter=end_chapter,
                volume_filter=volume_filter,
                quality=quality,
                template_id=template_id
            )
            
            return JsonResponse({
                'success': True,
                'batch_download': {
                    'id': batch_download.id,
                    'name': batch_download.name,
                    'status': batch_download.status,
                    'total_chapters': batch_download.total_chapters,
                    'progress_percentage': batch_download.progress_percentage,
                    'manga': {
                        'id': batch_download.manga.id,
                        'title': batch_download.manga.title,
                    }
                }
            })
            
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'error': 'Erro interno do servidor'}, status=500)
    
    def get(self, request: HttpRequest) -> JsonResponse:
        """Obtém downloads em lote do usuário."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Usuário não autenticado'}, status=401)
        
        status_filter = request.GET.get('status')
        batch_downloads = batch_download_service.get_user_batch_downloads(request.user, status_filter)
        
        batch_list = []
        for batch in batch_downloads:
            batch_data = {
                'id': batch.id,
                'name': batch.name,
                'status': batch.status,
                'progress_percentage': batch.progress_percentage,
                'total_chapters': batch.total_chapters,
                'completed_chapters': batch.completed_chapters,
                'failed_chapters': batch.failed_chapters,
                'total_size_mb': batch.total_size_mb,
                'downloaded_size_mb': batch.downloaded_size_mb,
                'created_at': batch.created_at.isoformat(),
                'started_at': batch.started_at.isoformat() if batch.started_at else None,
                'completed_at': batch.completed_at.isoformat() if batch.completed_at else None,
                'expires_at': batch.expires_at.isoformat() if batch.expires_at else None,
                'is_available': batch.is_available,
                'download_url': batch.get_file_url(),
                'manga': {
                    'id': batch.manga.id,
                    'title': batch.manga.title,
                }
            }
            batch_list.append(batch_data)
        
        return JsonResponse({
            'batch_downloads': batch_list
        })

@method_decorator(csrf_exempt, name='dispatch')
class BatchDownloadDetailView(DownloadAPIView):
    """
    API para operações em downloads em lote específicos.
    """
    
    def get(self, request: HttpRequest, batch_id: int) -> JsonResponse:
        """Obtém status detalhado de um download em lote."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Usuário não autenticado'}, status=401)
        
        try:
            status = batch_download_service.get_batch_download_status(batch_id, request.user)
            return JsonResponse({'status': status})
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=404)
        except Exception as e:
            return JsonResponse({'error': 'Erro interno do servidor'}, status=500)
    
    def delete(self, request: HttpRequest, batch_id: int) -> JsonResponse:
        """Remove um download em lote."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Usuário não autenticado'}, status=401)
        
        try:
            success = batch_download_service.delete_batch_download(batch_id, request.user)
            return JsonResponse({'success': success})
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=404)
        except Exception as e:
            return JsonResponse({'error': 'Erro interno do servidor'}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class BatchDownloadControlView(DownloadAPIView):
    """
    API para controle de downloads em lote (pausar, retomar, cancelar).
    """
    
    def post(self, request: HttpRequest, batch_id: int) -> JsonResponse:
        """Controla um download em lote."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Usuário não autenticado'}, status=401)
        
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            if action == 'pause':
                success = batch_download_service.pause_batch_download(batch_id, request.user)
            elif action == 'resume':
                success = batch_download_service.resume_batch_download(batch_id, request.user)
            elif action == 'cancel':
                success = batch_download_service.cancel_batch_download(batch_id, request.user)
            else:
                return JsonResponse({'error': 'Ação inválida'}, status=400)
            
            return JsonResponse({'success': success})
            
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=404)
        except Exception as e:
            return JsonResponse({'error': 'Erro interno do servidor'}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class BatchDownloadTemplateView(DownloadAPIView):
    """
    API para templates de download em lote.
    """
    
    def get(self, request: HttpRequest) -> JsonResponse:
        """Obtém templates de download."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Usuário não autenticado'}, status=401)
        
        user_templates = batch_download_service.get_user_templates(request.user)
        public_templates = batch_download_service.get_public_templates()
        
        def serialize_template(template):
            return {
                'id': template.id,
                'name': template.name,
                'description': template.description,
                'quality': template.quality,
                'max_concurrent_downloads': template.max_concurrent_downloads,
                'retry_failed': template.retry_failed,
                'max_retries': template.max_retries,
                'default_volume_filter': template.default_volume_filter,
                'include_unpublished': template.include_unpublished,
                'is_public': template.is_public,
                'created_at': template.created_at.isoformat(),
            }
        
        return JsonResponse({
            'user_templates': [serialize_template(t) for t in user_templates],
            'public_templates': [serialize_template(t) for t in public_templates]
        })
    
    def post(self, request: HttpRequest) -> JsonResponse:
        """Cria um novo template."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Usuário não autenticado'}, status=401)
        
        try:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            description = data.get('description', '').strip()
            quality = data.get('quality', 'original')
            max_concurrent_downloads = data.get('max_concurrent_downloads', 3)
            retry_failed = data.get('retry_failed', True)
            max_retries = data.get('max_retries', 3)
            default_volume_filter = data.get('default_volume_filter', '').strip()
            include_unpublished = data.get('include_unpublished', False)
            is_public = data.get('is_public', False)
            
            if not name:
                return JsonResponse({'error': 'Nome do template é obrigatório'}, status=400)
            
            # Criar template
            template = batch_download_service.create_batch_template(
                user=request.user,
                name=name,
                description=description,
                quality=quality,
                max_concurrent_downloads=max_concurrent_downloads,
                retry_failed=retry_failed,
                max_retries=max_retries,
                default_volume_filter=default_volume_filter,
                include_unpublished=include_unpublished
            )
            
            return JsonResponse({
                'success': True,
                'template': {
                    'id': template.id,
                    'name': template.name,
                    'description': template.description,
                    'quality': template.quality,
                    'max_concurrent_downloads': template.max_concurrent_downloads,
                    'retry_failed': template.retry_failed,
                    'max_retries': template.max_retries,
                    'default_volume_filter': template.default_volume_filter,
                    'include_unpublished': template.include_unpublished,
                    'is_public': template.is_public,
                    'created_at': template.created_at.isoformat(),
                }
            })
            
        except Exception as e:
            return JsonResponse({'error': 'Erro interno do servidor'}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class BatchDownloadStatsView(DownloadAPIView):
    """
    API para estatísticas de downloads em lote.
    """
    
    def get(self, request: HttpRequest) -> JsonResponse:
        """Obtém estatísticas de downloads em lote do usuário."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Usuário não autenticado'}, status=401)
        
        stats = batch_download_service.get_batch_download_stats(request.user)
        
        return JsonResponse({
            'stats': stats
        }) 