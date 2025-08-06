"""Service dedicado para operações de progresso de leitura
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
