"""
Serviço de Recomendações para Mangás
Baseado no comportamento de leitura e preferências dos usuários
"""

import logging
from typing import List, Dict, Any
from django.db.models import Q, Count, Avg
from django.contrib.auth import get_user_model
from django.core.cache import cache

from ..models.manga import Manga
from ..models.reading_progress import ReadingProgress
from ..models.user_lists import UserListEntry, Favorite

logger = logging.getLogger(__name__)
User = get_user_model()

class RecommendationService:
    """
    Serviço para gerar recomendações personalizadas de mangás.
    
    Estratégias de recomendação:
    1. Baseada em mangás similares que o usuário leu
    2. Baseada em gêneros preferidos
    3. Baseada em autores favoritos
    4. Baseada em mangás populares entre usuários similares
    5. Baseada em mangás recém-adicionados
    """
    
    def __init__(self):
        self.cache_timeout = 3600  # 1 hora
    
    def get_recommendations_for_user(self, user: User, limit: int = 10) -> List[Manga]:
        """
        Gera recomendações personalizadas para um usuário.
        """
        if not user.is_authenticated:
            return self.get_popular_mangas(limit)
        
        cache_key = f'manga_recommendations_{user.id}'
        recommendations = cache.get(cache_key)
        
        if recommendations is None:
            recommendations = self._generate_recommendations(user, limit)
            cache.set(cache_key, recommendations, self.cache_timeout)
        
        return recommendations
    
    def _generate_recommendations(self, user: User, limit: int) -> List[Manga]:
        """
        Gera recomendações usando múltiplas estratégias.
        """
        recommendations = []
        
        # 1. Baseado em mangás que o usuário leu e gostou
        similar_manga_recs = self._get_similar_manga_recommendations(user, limit // 3)
        recommendations.extend(similar_manga_recs)
        
        # 2. Baseado em gêneros preferidos
        genre_recs = self._get_genre_based_recommendations(user, limit // 3)
        recommendations.extend(genre_recs)
        
        # 3. Baseado em autores favoritos
        author_recs = self._get_author_based_recommendations(user, limit // 4)
        recommendations.extend(author_recs)
        
        # 4. Mangás populares entre usuários similares
        popular_recs = self._get_popular_among_similar_users(user, limit // 4)
        recommendations.extend(popular_recs)
        
        # Remover duplicatas e limitar
        seen_ids = set()
        unique_recommendations = []
        
        for manga in recommendations:
            if manga.id not in seen_ids and len(unique_recommendations) < limit:
                unique_recommendations.append(manga)
                seen_ids.add(manga.id)
        
        # Se não temos recomendações suficientes, adicionar mangás populares
        if len(unique_recommendations) < limit:
            popular_mangas = self.get_popular_mangas(limit - len(unique_recommendations))
            for manga in popular_mangas:
                if manga.id not in seen_ids:
                    unique_recommendations.append(manga)
                    seen_ids.add(manga.id)
        
        return unique_recommendations
    
    def _get_similar_manga_recommendations(self, user: User, limit: int) -> List[Manga]:
        """
        Encontra mangás similares aos que o usuário leu e gostou.
        """
        # Obter mangás que o usuário leu completamente
        completed_mangas = ReadingProgress.objects.filter(
            user=user,
            is_completed=True
        ).values_list('manga_id', flat=True)
        
        if not completed_mangas:
            return []
        
        # Encontrar usuários que também leram esses mangás
        similar_users = ReadingProgress.objects.filter(
            manga_id__in=completed_mangas,
            is_completed=True
        ).exclude(user=user).values_list('user_id', flat=True).distinct()
        
        if not similar_users:
            return []
        
        # Obter mangás que esses usuários gostaram
        similar_mangas = ReadingProgress.objects.filter(
            user_id__in=similar_users,
            is_completed=True
        ).exclude(manga_id__in=completed_mangas).values('manga_id').annotate(
            reader_count=Count('user_id', distinct=True)
        ).order_by('-reader_count')[:limit * 2]
        
        manga_ids = [item['manga_id'] for item in similar_mangas]
        return list(Manga.objects.filter(id__in=manga_ids, is_published=True))
    
    def _get_genre_based_recommendations(self, user: User, limit: int) -> List[Manga]:
        """
        Recomenda mangás baseado nos gêneros que o usuário prefere.
        """
        # Obter gêneros dos mangás que o usuário leu
        read_mangas = ReadingProgress.objects.filter(
            user=user,
            is_completed=True
        ).values_list('manga_id', flat=True)
        
        if not read_mangas:
            return []
        
        # Aqui você pode implementar lógica baseada em gêneros
        # Por enquanto, vamos retornar mangás populares
        return self.get_popular_mangas(limit)
    
    def _get_author_based_recommendations(self, user: User, limit: int) -> List[Manga]:
        """
        Recomenda mangás do mesmo autor.
        """
        # Obter autores dos mangás favoritos
        favorite_mangas = Favorite.objects.filter(user=user).values_list('manga_id', flat=True)
        
        if not favorite_mangas:
            return []
        
        # Obter autores
        authors = Manga.objects.filter(id__in=favorite_mangas).values_list('author', flat=True)
        authors = [author for author in authors if author]
        
        if not authors:
            return []
        
        # Encontrar outros mangás dos mesmos autores
        return list(Manga.objects.filter(
            author__in=authors,
            is_published=True
        ).exclude(id__in=favorite_mangas)[:limit])
    
    def _get_popular_among_similar_users(self, user: User, limit: int) -> List[Manga]:
        """
        Encontra mangás populares entre usuários com gostos similares.
        """
        # Obter mangás que o usuário leu
        user_mangas = ReadingProgress.objects.filter(user=user).values_list('manga_id', flat=True)
        
        if not user_mangas:
            return self.get_popular_mangas(limit)
        
        # Encontrar usuários que leram os mesmos mangás
        similar_users = ReadingProgress.objects.filter(
            manga_id__in=user_mangas
        ).exclude(user=user).values_list('user_id', flat=True).distinct()
        
        if not similar_users:
            return self.get_popular_mangas(limit)
        
        # Obter mangás populares entre esses usuários
        popular_mangas = ReadingProgress.objects.filter(
            user_id__in=similar_users,
            is_completed=True
        ).exclude(manga_id__in=user_mangas).values('manga_id').annotate(
            reader_count=Count('user_id', distinct=True)
        ).order_by('-reader_count')[:limit]
        
        manga_ids = [item['manga_id'] for item in popular_mangas]
        return list(Manga.objects.filter(id__in=manga_ids, is_published=True))
    
    def get_popular_mangas(self, limit: int = 10) -> List[Manga]:
        """
        Retorna os mangás mais populares baseado em visualizações e leituras.
        """
        cache_key = f'popular_mangas_{limit}'
        popular_mangas = cache.get(cache_key)
        
        if popular_mangas is None:
            popular_mangas = list(Manga.objects.filter(
                is_published=True
            ).annotate(
                read_count=Count('reading_progress', distinct=True),
                favorite_count=Count('favorited_by', distinct=True)
            ).order_by('-read_count', '-favorite_count')[:limit])
            
            cache.set(cache_key, popular_mangas, self.cache_timeout)
        
        return popular_mangas
    
    def get_recently_added_mangas(self, limit: int = 10) -> List[Manga]:
        """
        Retorna mangás adicionados recentemente.
        """
        return list(Manga.objects.filter(
            is_published=True
        ).order_by('-created_at')[:limit])
    
    def get_trending_mangas(self, limit: int = 10) -> List[Manga]:
        """
        Retorna mangás em tendência (muitas leituras recentes).
        """
        from django.utils import timezone
        from datetime import timedelta
        
        # Últimos 7 dias
        recent_date = timezone.now() - timedelta(days=7)
        
        trending_mangas = Manga.objects.filter(
            is_published=True,
            reading_progress__last_read_at__gte=recent_date
        ).annotate(
            recent_reads=Count('reading_progress')
        ).order_by('-recent_reads')[:limit]
        
        return list(trending_mangas)
    
    def get_mangas_for_new_users(self, limit: int = 10) -> List[Manga]:
        """
        Recomendações para novos usuários (mangás populares e bem avaliados).
        """
        return list(Manga.objects.filter(
            is_published=True
        ).annotate(
            avg_rating=Avg('list_entries__rating'),
            read_count=Count('reading_progress', distinct=True)
        ).filter(
            avg_rating__gte=4.0,
            read_count__gte=10
        ).order_by('-avg_rating', '-read_count')[:limit])
    
    def get_similar_mangas(self, manga: Manga, limit: int = 5) -> List[Manga]:
        """
        Encontra mangás similares a um mangá específico.
        """
        # Usuários que leram este mangá
        readers = ReadingProgress.objects.filter(
            manga=manga,
            is_completed=True
        ).values_list('user_id', flat=True)
        
        if not readers:
            return []
        
        # Outros mangás que esses usuários leram
        similar_mangas = ReadingProgress.objects.filter(
            user_id__in=readers,
            is_completed=True
        ).exclude(manga=manga).values('manga_id').annotate(
            reader_count=Count('user_id', distinct=True)
        ).order_by('-reader_count')[:limit]
        
        manga_ids = [item['manga_id'] for item in similar_mangas]
        return list(Manga.objects.filter(id__in=manga_ids, is_published=True))
    
    def clear_user_recommendations_cache(self, user: User):
        """
        Limpa o cache de recomendações de um usuário.
        """
        cache_key = f'manga_recommendations_{user.id}'
        cache.delete(cache_key)
    
    def get_user_reading_stats(self, user: User) -> Dict[str, Any]:
        """
        Retorna estatísticas de leitura do usuário.
        """
        if not user.is_authenticated:
            return {}
        
        stats = {
            'total_mangas_read': ReadingProgress.objects.filter(
                user=user,
                is_completed=True
            ).values('manga').distinct().count(),
            
            'total_chapters_read': ReadingProgress.objects.filter(
                user=user,
                is_completed=True
            ).count(),
            
            'total_reading_time': ReadingProgress.objects.filter(
                user=user
            ).aggregate(
                total_time=models.Sum('reading_time')
            )['total_time'] or 0,
            
            'favorite_mangas': Favorite.objects.filter(user=user).count(),
            
            'reading_lists': UserList.objects.filter(user=user).count(),
        }
        
        return stats 