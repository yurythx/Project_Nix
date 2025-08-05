from django.db.models import Avg, Sum, Count, Q
from django.utils import timezone
from datetime import timedelta, datetime
from ..models.analytics import ReadingSession, ReadingStatistics, BookAnalytics, ReadingGoal
from ..models.book import Book
from django.contrib.auth import get_user_model

User = get_user_model()


class AnalyticsService:
    @staticmethod
    def start_reading_session(user, book, device_type='desktop', location=''):
        """Inicia uma nova sessão de leitura"""
        # Finaliza qualquer sessão ativa do usuário
        active_sessions = ReadingSession.objects.filter(
            user=user, 
            end_time__isnull=True
        )
        for session in active_sessions:
            session.end_time = timezone.now()
            session.save()
        
        # Cria nova sessão
        session = ReadingSession.objects.create(
            user=user,
            book=book,
            device_type=device_type,
            location=location
        )
        return session
    
    @staticmethod
    def end_reading_session(session_id, pages_read=0, current_page=1):
        """Finaliza uma sessão de leitura"""
        try:
            session = ReadingSession.objects.get(id=session_id, end_time__isnull=True)
            session.end_time = timezone.now()
            session.pages_read = pages_read
            session.current_page = current_page
            
            # Calcula velocidade de leitura (estimativa)
            if session.duration and session.pages_read > 0:
                minutes = session.duration.total_seconds() / 60
                # Estimativa: 250 palavras por página
                words_read = session.pages_read * 250
                if minutes > 0:
                    session.reading_speed = words_read / minutes
            
            session.save()
            
            # Atualiza estatísticas do usuário
            AnalyticsService.update_user_statistics(session.user)
            
            # Atualiza analytics do livro
            AnalyticsService.update_book_analytics(session.book)
            
            return session
        except ReadingSession.DoesNotExist:
            return None
    
    @staticmethod
    def update_reading_location(session_id, current_page, pages_read=None):
        """Atualiza a localização atual de leitura"""
        try:
            session = ReadingSession.objects.get(id=session_id, end_time__isnull=True)
            session.current_page = current_page
            if pages_read is not None:
                session.pages_read = pages_read
            session.save()
            return session
        except ReadingSession.DoesNotExist:
            return None
    
    @staticmethod
    def get_active_session(user):
        """Retorna a sessão ativa do usuário"""
        return ReadingSession.objects.filter(
            user=user, 
            end_time__isnull=True
        ).first()
    
    @staticmethod
    def update_user_statistics(user):
        """Atualiza as estatísticas do usuário"""
        stats, created = ReadingStatistics.objects.get_or_create(user=user)
        stats.update_statistics()
        return stats
    
    @staticmethod
    def update_book_analytics(book):
        """Atualiza as analytics do livro"""
        analytics, created = BookAnalytics.objects.get_or_create(book=book)
        analytics.update_analytics()
        return analytics
    
    @staticmethod
    def get_user_dashboard_data(user):
        """Retorna dados para o dashboard do usuário"""
        # Estatísticas gerais
        stats, _ = ReadingStatistics.objects.get_or_create(user=user)
        
        # Sessões recentes
        recent_sessions = ReadingSession.objects.filter(
            user=user,
            end_time__isnull=False
        ).order_by('-start_time')[:10]
        
        # Progresso de leitura dos últimos 7 dias
        seven_days_ago = timezone.now().date() - timedelta(days=7)
        daily_progress = []
        
        for i in range(7):
            date = seven_days_ago + timedelta(days=i)
            sessions_day = ReadingSession.objects.filter(
                user=user,
                start_time__date=date,
                end_time__isnull=False
            )
            
            total_pages = sum(s.pages_read for s in sessions_day)
            total_minutes = sum(s.duration_minutes for s in sessions_day)
            
            daily_progress.append({
                'date': date.strftime('%Y-%m-%d'),
                'pages': total_pages,
                'minutes': int(total_minutes)
            })
        
        # Metas ativas
        active_goals = ReadingGoal.objects.filter(
            user=user,
            status='active'
        ).order_by('-created_at')
        
        # Livros em progresso
        books_in_progress = ReadingSession.objects.filter(
            user=user
        ).values('book').annotate(
            total_pages_read=Sum('pages_read'),
            last_session=timezone.now()
        ).order_by('-last_session')[:5]
        
        return {
            'statistics': stats,
            'recent_sessions': recent_sessions,
            'daily_progress': daily_progress,
            'active_goals': active_goals,
            'books_in_progress': books_in_progress
        }
    
    @staticmethod
    def get_reading_trends(user, days=30):
        """Retorna tendências de leitura do usuário"""
        start_date = timezone.now().date() - timedelta(days=days)
        
        sessions = ReadingSession.objects.filter(
            user=user,
            start_time__date__gte=start_date,
            end_time__isnull=False
        )
        
        # Tendências por dia da semana
        weekday_stats = {}
        for i in range(7):
            weekday_sessions = sessions.filter(start_time__week_day=i+1)
            weekday_stats[i] = {
                'sessions': weekday_sessions.count(),
                'total_minutes': sum(s.duration_minutes for s in weekday_sessions),
                'avg_pages': weekday_sessions.aggregate(Avg('pages_read'))['pages_read__avg'] or 0
            }
        
        # Tendências por hora do dia
        hourly_stats = {}
        for hour in range(24):
            hour_sessions = sessions.filter(start_time__hour=hour)
            hourly_stats[hour] = {
                'sessions': hour_sessions.count(),
                'total_minutes': sum(s.duration_minutes for s in hour_sessions)
            }
        
        return {
            'weekday_stats': weekday_stats,
            'hourly_stats': hourly_stats,
            'total_sessions': sessions.count(),
            'total_books': sessions.values('book').distinct().count()
        }
    
    @staticmethod
    def create_reading_goal(user, goal_type, target_value, end_date, description=''):
        """Cria uma nova meta de leitura"""
        goal = ReadingGoal.objects.create(
            user=user,
            goal_type=goal_type,
            target_value=target_value,
            end_date=end_date,
            description=description
        )
        goal.update_progress()
        return goal
    
    @staticmethod
    def update_all_goals(user):
        """Atualiza o progresso de todas as metas ativas do usuário"""
        active_goals = ReadingGoal.objects.filter(user=user, status='active')
        for goal in active_goals:
            goal.update_progress()
        return active_goals