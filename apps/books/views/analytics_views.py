from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone
from datetime import datetime
import json

from ..models.book import Book
from ..models.analytics import ReadingSession, ReadingGoal
from ..services.analytics_service import AnalyticsService


@method_decorator(login_required, name='dispatch')
class ReadingDashboardView(View):
    def get(self, request):
        """Renderiza o dashboard de analytics"""
        dashboard_data = AnalyticsService.get_user_dashboard_data(request.user)
        return render(request, 'books/reading_dashboard.html', dashboard_data)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def start_reading_session(request):
    """Inicia uma nova sessão de leitura"""
    try:
        data = json.loads(request.body)
        book_id = data.get('book_id')
        device_type = data.get('device_type', 'desktop')
        location = data.get('location', '')
        
        book = get_object_or_404(Book, id=book_id)
        session = AnalyticsService.start_reading_session(
            user=request.user,
            book=book,
            device_type=device_type,
            location=location
        )
        
        return JsonResponse({
            'success': True,
            'session_id': session.id,
            'message': 'Sessão de leitura iniciada com sucesso'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def end_reading_session(request):
    """Finaliza uma sessão de leitura"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        pages_read = data.get('pages_read', 0)
        current_page = data.get('current_page', 1)
        
        session = AnalyticsService.end_reading_session(
            session_id=session_id,
            pages_read=pages_read,
            current_page=current_page
        )
        
        if session:
            return JsonResponse({
                'success': True,
                'duration_minutes': session.duration_minutes,
                'message': 'Sessão finalizada com sucesso'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Sessão não encontrada'
            }, status=404)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def update_reading_location(request):
    """Atualiza a localização de leitura"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        current_page = data.get('current_page')
        pages_read = data.get('pages_read')
        
        session = AnalyticsService.update_reading_location(
            session_id=session_id,
            current_page=current_page,
            pages_read=pages_read
        )
        
        if session:
            return JsonResponse({
                'success': True,
                'message': 'Localização atualizada'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Sessão não encontrada'
            }, status=404)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
def reading_trends(request):
    """Retorna tendências de leitura do usuário"""
    days = int(request.GET.get('days', 30))
    trends = AnalyticsService.get_reading_trends(request.user, days)
    return JsonResponse(trends)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def create_reading_goal(request):
    """Cria uma nova meta de leitura"""
    try:
        data = json.loads(request.body)
        goal_type = data.get('goal_type')
        target_value = int(data.get('target_value'))
        end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()
        description = data.get('description', '')
        
        goal = AnalyticsService.create_reading_goal(
            user=request.user,
            goal_type=goal_type,
            target_value=target_value,
            end_date=end_date,
            description=description
        )
        
        return JsonResponse({
            'success': True,
            'goal_id': goal.id,
            'message': 'Meta criada com sucesso'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
def user_statistics(request):
    """Retorna estatísticas detalhadas do usuário"""
    stats = AnalyticsService.update_user_statistics(request.user)
    
    return JsonResponse({
        'total_reading_time_hours': stats.total_reading_time.total_seconds() / 3600,
        'total_pages_read': stats.total_pages_read,
        'total_books_completed': stats.total_books_completed,
        'average_reading_speed': stats.average_reading_speed,
        'current_streak': stats.current_streak,
        'best_streak': stats.best_streak,
        'longest_session_minutes': stats.longest_session.total_seconds() / 60 if stats.longest_session else 0
    })


@login_required
def get_active_session(request):
    """Retorna a sessão ativa do usuário"""
    session = AnalyticsService.get_active_session(request.user)
    
    if session:
        return JsonResponse({
            'has_active_session': True,
            'session_id': session.id,
            'book_title': session.book.title,
            'start_time': session.start_time.isoformat(),
            'current_page': session.current_page
        })
    else:
        return JsonResponse({
            'has_active_session': False
        })