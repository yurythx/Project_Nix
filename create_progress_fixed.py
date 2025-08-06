import os

# Criar o ReadingProgressService
reading_progress_service_content = '''"""Service dedicado para operações de progresso de leitura
Gerencia o rastreamento e histórico de leitura dos usuários"""

import logging
from typing import Dict, Any, Optional, List
from django.db.models import QuerySet, Q, Count, Avg, Sum
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from ..models.reading_progress import ReadingProgress, ReadingHistory
from ..models.manga import Manga
from ..models.capitulo import Capitulo

logger = logging.getLogger(__name__)

class ReadingProgressService:
    """Service para operações de progresso de leitura"""
    
    def save_progress(self, user: User, manga: Manga, capitulo: Capitulo, 
                     current_page: int, total_pages: int, reading_time: int = 0) -> ReadingProgress:
        """Salva ou atualiza o progresso de leitura do usuário"""
        try:
            progress, created = ReadingProgress.objects.get_or_create(
                user=user,
                manga=manga,
                capitulo=capitulo,
                defaults={
                    'current_page': current_page,
                    'total_pages': total_pages,
                    'reading_time': reading_time
                }
            )
            
            if not created:
                progress.update_progress(current_page, reading_time)
            
            logger.info(f"Progresso salvo para usuário {user.id}, mangá {manga.id}, capítulo {capitulo.id}")
            return progress
            
        except Exception as e:
            logger.error(f"Erro ao salvar progresso: {e}")
            raise
    
    def get_progress(self, user: User, manga: Manga, capitulo: Optional[Capitulo] = None) -> Optional[ReadingProgress]:
        """Obtém o progresso de leitura do usuário"""
        try:
            queryset = ReadingProgress.objects.filter(user=user, manga=manga)
            
            if capitulo:
                return queryset.filter(capitulo=capitulo).first()
            else:
                # Retorna o progresso mais recente
                return queryset.order_by('-last_read_at').first()
                
        except Exception as e:
            logger.error(f"Erro ao obter progresso: {e}")
            return None
    
    def get_manga_statistics(self, user: User, manga: Manga) -> Dict[str, Any]:
        """Obtém estatísticas de leitura do mangá para o usuário"""
        try:
            progress_queryset = ReadingProgress.objects.filter(user=user, manga=manga)
            
            total_chapters = manga.get_total_chapters()
            completed_chapters = progress_queryset.filter(is_completed=True).count()
            total_reading_time = progress_queryset.aggregate(Sum('reading_time'))['reading_time__sum'] or 0
            
            # Último progresso
            last_progress = progress_queryset.order_by('-last_read_at').first()
            
            return {
                'total_chapters': total_chapters,
                'completed_chapters': completed_chapters,
                'completion_percentage': (completed_chapters / total_chapters * 100) if total_chapters > 0 else 0,
                'total_reading_time': total_reading_time,
                'last_chapter_read': last_progress.capitulo if last_progress else None,
                'last_read_at': last_progress.last_read_at if last_progress else None
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas do mangá: {e}")
            return {}
    
    def mark_chapter_completed(self, user: User, manga: Manga, capitulo: Capitulo, 
                              reading_time: int = 0) -> ReadingProgress:
        """Marca um capítulo como concluído"""
        try:
            progress, created = ReadingProgress.objects.get_or_create(
                user=user,
                manga=manga,
                capitulo=capitulo,
                defaults={
                    'current_page': capitulo.paginas.count(),
                    'total_pages': capitulo.paginas.count(),
                    'is_completed': True,
                    'reading_time': reading_time
                }
            )
            
            if not created:
                progress.mark_as_completed()
                if reading_time > 0:
                    progress.reading_time += reading_time
                    progress.save()
            
            # Criar entrada no histórico
            ReadingHistory.objects.create(
                user=user,
                manga=manga,
                capitulo=capitulo,
                completed_at=timezone.now(),
                session_duration=reading_time
            )
            
            logger.info(f"Capítulo {capitulo.id} marcado como concluído para usuário {user.id}")
            return progress
            
        except Exception as e:
            logger.error(f"Erro ao marcar capítulo como concluído: {e}")
            raise
    
    def get_continue_reading_suggestions(self, user: User, limit: int = 5) -> List[Dict[str, Any]]:
        """Obtém sugestões de continuação de leitura"""
        try:
            # Buscar progressos recentes (últimos 30 dias)
            recent_progress = ReadingProgress.objects.filter(
                user=user,
                last_read_at__gte=timezone.now() - timedelta(days=30)
            ).select_related('manga', 'capitulo').order_by('-last_read_at')[:limit]
            
            suggestions = []
            for progress in recent_progress:
                # Buscar próximo capítulo
                next_chapter = self._get_next_chapter(progress.capitulo)
                
                suggestions.append({
                    'manga': progress.manga,
                    'current_chapter': progress.capitulo,
                    'next_chapter': next_chapter,
                    'progress_percentage': progress.progress_percentage,
                    'last_read_at': progress.last_read_at
                })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Erro ao obter sugestões de continuação: {e}")
            return []
    
    def _get_next_chapter(self, current_chapter: Capitulo) -> Optional[Capitulo]:
        """Obtém o próximo capítulo na sequência"""
        try:
            # Primeiro, tentar próximo capítulo no mesmo volume
            next_in_volume = Capitulo.objects.filter(
                volume=current_chapter.volume,
                numero__gt=current_chapter.numero,
                is_published=True
            ).order_by('numero').first()
            
            if next_in_volume:
                return next_in_volume
            
            # Se não há próximo no volume, buscar primeiro capítulo do próximo volume
            next_volume = current_chapter.volume.manga.volumes.filter(
                numero__gt=current_chapter.volume.numero,
                is_published=True
            ).order_by('numero').first()
            
            if next_volume:
                return next_volume.capitulos.filter(
                    is_published=True
                ).order_by('numero').first()
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao obter próximo capítulo: {e}")
            return None

# Instância global do serviço
reading_progress_service = ReadingProgressService()
'''

# Criar o arquivo do serviço
with open('apps/mangas/services/reading_progress_service.py', 'w', encoding='utf-8') as f:
    f.write(reading_progress_service_content)

print("✅ ReadingProgressService criado!")

# Criar as Progress Views
progress_views_content = '''"""Views para operações de progresso de leitura via AJAX"""

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
'''

# Criar o arquivo das views
with open('apps/mangas/views/progress_views.py', 'w', encoding='utf-8') as f:
    f.write(progress_views_content)

print("✅ Progress Views criadas!")
print("\n🎉 Todos os arquivos foram criados com sucesso!")
print("\n📋 Próximos passos:")
print("1. Adicionar as URLs ao urls.py")
print("2. Atualizar o __init__.py dos serviços")
print("3. Atualizar o admin.py")
print("4. Executar as migrações se necessário")