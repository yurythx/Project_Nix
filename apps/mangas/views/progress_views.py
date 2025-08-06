"""Views para operações de progresso de leitura via AJAX"""

import json
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View

from ..models.manga import Manga
from ..models.capitulo import Capitulo
from ..services.reading_progress_service import reading_progress_service

logger = logging.getLogger(__name__)

@login_required
@require_http_methods(["POST"])
def save_progress(request):
    """Salva o progresso de leitura do usuário"""
    try:
        data = json.loads(request.body)
        
        manga = get_object_or_404(Manga, id=data.get('manga_id'))
        capitulo = get_object_or_404(Capitulo, id=data.get('capitulo_id'))
        current_page = int(data.get('current_page', 1))
        total_pages = int(data.get('total_pages', 1))
        reading_time = int(data.get('reading_time', 0))
        
        progress = reading_progress_service.save_progress(
            user=request.user,
            manga=manga,
            capitulo=capitulo,
            current_page=current_page,
            total_pages=total_pages,
            reading_time=reading_time
        )
        
        return JsonResponse({
            'success': True,
            'progress_percentage': progress.progress_percentage,
            'message': 'Progresso salvo com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro ao salvar progresso: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Erro interno do servidor'
        }, status=500)

@login_required
@require_http_methods(["GET"])
def get_progress(request):
    """Obtém o progresso de leitura do usuário"""
    try:
        manga_id = request.GET.get('manga_id')
        capitulo_id = request.GET.get('capitulo_id')
        
        manga = get_object_or_404(Manga, id=manga_id)
        capitulo = None
        
        if capitulo_id:
            capitulo = get_object_or_404(Capitulo, id=capitulo_id)
        
        progress = reading_progress_service.get_progress(
            user=request.user,
            manga=manga,
            capitulo=capitulo
        )
        
        if progress:
            return JsonResponse({
                'success': True,
                'current_page': progress.current_page,
                'total_pages': progress.total_pages,
                'progress_percentage': progress.progress_percentage,
                'is_completed': progress.is_completed,
                'last_read_at': progress.last_read_at.isoformat()
            })
        else:
            return JsonResponse({
                'success': True,
                'current_page': 1,
                'total_pages': 1,
                'progress_percentage': 0,
                'is_completed': False,
                'last_read_at': None
            })
            
    except Exception as e:
        logger.error(f"Erro ao obter progresso: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Erro interno do servidor'
        }, status=500)

@login_required
@require_http_methods(["GET"])
def get_manga_statistics(request):
    """Obtém estatísticas de leitura do mangá"""
    try:
        manga_id = request.GET.get('manga_id')
        manga = get_object_or_404(Manga, id=manga_id)
        
        stats = reading_progress_service.get_manga_statistics(
            user=request.user,
            manga=manga
        )
        
        # Preparar resposta
        response_data = {
            'success': True,
            'total_chapters': stats.get('total_chapters', 0),
            'completed_chapters': stats.get('completed_chapters', 0),
            'completion_percentage': stats.get('completion_percentage', 0),
            'total_reading_time': stats.get('total_reading_time', 0),
            'last_read_at': stats.get('last_read_at').isoformat() if stats.get('last_read_at') else None
        }
        
        if stats.get('last_chapter_read'):
            response_data['last_chapter_read'] = {
                'id': stats['last_chapter_read'].id,
                'titulo': stats['last_chapter_read'].titulo,
                'numero': stats['last_chapter_read'].numero
            }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Erro interno do servidor'
        }, status=500)

@login_required
@require_http_methods(["POST"])
def mark_chapter_completed(request):
    """Marca um capítulo como concluído"""
    try:
        data = json.loads(request.body)
        
        manga = get_object_or_404(Manga, id=data.get('manga_id'))
        capitulo = get_object_or_404(Capitulo, id=data.get('capitulo_id'))
        reading_time = int(data.get('reading_time', 0))
        
        progress = reading_progress_service.mark_chapter_completed(
            user=request.user,
            manga=manga,
            capitulo=capitulo,
            reading_time=reading_time
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Capítulo marcado como concluído',
            'progress_percentage': progress.progress_percentage
        })
        
    except Exception as e:
        logger.error(f"Erro ao marcar capítulo como concluído: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Erro interno do servidor'
        }, status=500)

@login_required
@require_http_methods(["GET"])
def continue_reading_suggestions(request):
    """Obtém sugestões de continuação de leitura"""
    try:
        limit = int(request.GET.get('limit', 5))
        
        suggestions = reading_progress_service.get_continue_reading_suggestions(
            user=request.user,
            limit=limit
        )
        
        # Preparar resposta
        response_data = {
            'success': True,
            'suggestions': []
        }
        
        for suggestion in suggestions:
            suggestion_data = {
                'manga': {
                    'id': suggestion['manga'].id,
                    'titulo': suggestion['manga'].titulo,
                    'slug': suggestion['manga'].slug,
                    'capa_url': suggestion['manga'].capa.url if suggestion['manga'].capa else None
                },
                'current_chapter': {
                    'id': suggestion['current_chapter'].id,
                    'titulo': suggestion['current_chapter'].titulo,
                    'numero': suggestion['current_chapter'].numero
                },
                'progress_percentage': suggestion['progress_percentage'],
                'last_read_at': suggestion['last_read_at'].isoformat()
            }
            
            if suggestion['next_chapter']:
                suggestion_data['next_chapter'] = {
                    'id': suggestion['next_chapter'].id,
                    'titulo': suggestion['next_chapter'].titulo,
                    'numero': suggestion['next_chapter'].numero,
                    'slug': suggestion['next_chapter'].slug
                }
            
            response_data['suggestions'].append(suggestion_data)
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Erro ao obter sugestões: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Erro interno do servidor'
        }, status=500)
