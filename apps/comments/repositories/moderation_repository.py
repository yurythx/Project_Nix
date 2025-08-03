from typing import List, Optional, Dict, Any
from django.contrib.auth import get_user_model
from django.db.models import QuerySet, Q, Count
from django.db import transaction
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from ..interfaces.repositories import IModerationRepository
from ..models import Comment, CommentModeration, ModerationAction, ModerationQueue

User = get_user_model()


class DjangoModerationRepository(IModerationRepository):
    """
    Implementação Django do repositório de moderação
    
    Implementa IModerationRepository seguindo os princípios SOLID
    """
    
    def get_moderation_config(self, app_label: str, model_name: str) -> Optional[CommentModeration]:
        """Busca configuração de moderação"""
        try:
            return CommentModeration.objects.get(
                app_label=app_label,
                model_name=model_name,
                is_active=True
            )
        except CommentModeration.DoesNotExist:
            return None
    
    @transaction.atomic
    def create_moderation_config(self, **kwargs) -> CommentModeration:
        """Cria configuração de moderação"""
        return CommentModeration.objects.create(**kwargs)
    
    @transaction.atomic
    def update_moderation_config(self, config: CommentModeration, **kwargs) -> CommentModeration:
        """Atualiza configuração de moderação"""
        for field, value in kwargs.items():
            setattr(config, field, value)
        
        config.save()
        return config
    
    def get_moderation_queue(self, assigned_to: Optional[User] = None) -> QuerySet:
        """Busca fila de moderação"""
        queryset = ModerationQueue.objects.select_related(
            'comment__author',
            'comment__content_type',
            'assigned_to'
        ).filter(
            comment__status='pending'
        )
        
        if assigned_to:
            queryset = queryset.filter(assigned_to=assigned_to)
        
        return queryset.order_by('-priority', '-reports_count', 'created_at')
    
    @transaction.atomic
    def add_to_queue(self, comment: Comment, priority: str = 'normal') -> ModerationQueue:
        """Adiciona comentário à fila de moderação"""
        queue_item, created = ModerationQueue.objects.get_or_create(
            comment=comment,
            defaults={'priority': priority}
        )
        
        if not created and queue_item.priority != priority:
            queue_item.priority = priority
            queue_item.save(update_fields=['priority', 'updated_at'])
        
        return queue_item
    
    @transaction.atomic
    def remove_from_queue(self, comment: Comment) -> bool:
        """Remove comentário da fila de moderação"""
        deleted, _ = ModerationQueue.objects.filter(comment=comment).delete()
        return deleted > 0
    
    @transaction.atomic
    def assign_to_moderator(self, queue_item: ModerationQueue, moderator: User) -> ModerationQueue:
        """Atribui item da fila a moderador"""
        queue_item.assigned_to = moderator
        queue_item.save(update_fields=['assigned_to', 'updated_at'])
        return queue_item
    
    @transaction.atomic
    def create_moderation_action(self, **kwargs) -> ModerationAction:
        """Cria registro de ação de moderação"""
        return ModerationAction.objects.create(**kwargs)
    
    def get_moderation_history(self, comment: Comment) -> QuerySet:
        """Busca histórico de moderação"""
        return ModerationAction.objects.filter(
            comment=comment
        ).select_related(
            'moderator'
        ).order_by('-created_at')
    
    def get_moderator_stats(self, moderator: User, period_days: int = 30) -> Dict[str, int]:
        """Busca estatísticas do moderador"""
        since = timezone.now() - timezone.timedelta(days=period_days)
        
        actions = ModerationAction.objects.filter(
            moderator=moderator,
            created_at__gte=since
        )
        
        stats = actions.aggregate(
            total_actions=Count('id'),
            approved=Count('id', filter=Q(action='approved')),
            rejected=Count('id', filter=Q(action='rejected')),
            spam=Count('id', filter=Q(action='spam')),
            deleted=Count('id', filter=Q(action='deleted')),
        )
        
        # Adiciona estatísticas da fila
        queue_stats = ModerationQueue.objects.filter(
            assigned_to=moderator
        ).aggregate(
            assigned_items=Count('id'),
            high_priority=Count('id', filter=Q(priority='high')),
            urgent_items=Count('id', filter=Q(priority='urgent')),
        )
        
        stats.update(queue_stats)
        return stats
    
    def check_rate_limit(self, user: User, config: CommentModeration) -> bool:
        """Verifica limite de comentários do usuário"""
        now = timezone.now()
        
        # Verifica limite por hora
        hour_ago = now - timezone.timedelta(hours=1)
        comments_last_hour = Comment.objects.filter(
            author=user,
            created_at__gte=hour_ago
        ).count()
        
        if comments_last_hour >= config.max_comments_per_hour:
            return False
        
        # Verifica limite por dia
        day_ago = now - timezone.timedelta(days=1)
        comments_last_day = Comment.objects.filter(
            author=user,
            created_at__gte=day_ago
        ).count()
        
        if comments_last_day >= config.max_comments_per_day:
            return False
        
        return True
    
    def is_spam_suspected(self, content: str, user: User, ip_address: str) -> bool:
        """Verifica se comentário é suspeito de spam"""
        # Verifica padrões de spam básicos
        spam_indicators = 0
        
        # Muitas URLs
        if content.count('http') > 2:
            spam_indicators += 1
        
        # Muito texto em maiúsculas
        if len([c for c in content if c.isupper()]) > len(content) * 0.5:
            spam_indicators += 1
        
        # Muitos caracteres repetidos
        for char in '!@#$%':
            if content.count(char) > 5:
                spam_indicators += 1
                break
        
        # Verifica histórico do usuário
        recent_comments = Comment.objects.filter(
            author=user,
            created_at__gte=timezone.now() - timezone.timedelta(hours=1)
        ).count()
        
        if recent_comments > 10:
            spam_indicators += 2
        
        # Verifica IP
        ip_comments = Comment.objects.filter(
            ip_address=ip_address,
            created_at__gte=timezone.now() - timezone.timedelta(hours=1)
        ).count()
        
        if ip_comments > 15:
            spam_indicators += 2
        
        return spam_indicators >= 3
    
    def get_pending_by_priority(self, priority: str) -> QuerySet:
        """Busca comentários pendentes por prioridade"""
        return ModerationQueue.objects.filter(
            comment__status='pending',
            priority=priority
        ).select_related(
            'comment__author',
            'comment__content_type'
        ).order_by('created_at')
    
    def get_reported_comments(self) -> QuerySet:
        """Busca comentários reportados"""
        return ModerationQueue.objects.filter(
            is_reported=True
        ).select_related(
            'comment__author',
            'comment__content_type'
        ).order_by('-reports_count', 'created_at')
    
    def get_spam_suspected_comments(self) -> QuerySet:
        """Busca comentários suspeitos de spam"""
        return ModerationQueue.objects.filter(
            is_spam_suspected=True
        ).select_related(
            'comment__author',
            'comment__content_type'
        ).order_by('created_at')
    
    @transaction.atomic
    def bulk_assign_to_moderator(self, queue_ids: List[int], moderator: User) -> int:
        """Atribui múltiplos itens a um moderador"""
        updated = ModerationQueue.objects.filter(
            id__in=queue_ids
        ).update(
            assigned_to=moderator,
            updated_at=timezone.now()
        )
        
        return updated
    
    def get_moderation_workload(self) -> Dict[str, Any]:
        """Retorna estatísticas da carga de trabalho de moderação"""
        total_pending = ModerationQueue.objects.filter(
            comment__status='pending'
        ).count()
        
        by_priority = ModerationQueue.objects.filter(
            comment__status='pending'
        ).values('priority').annotate(
            count=Count('id')
        ).order_by('priority')
        
        assigned_count = ModerationQueue.objects.filter(
            comment__status='pending',
            assigned_to__isnull=False
        ).count()
        
        unassigned_count = total_pending - assigned_count
        
        # Tempo médio de moderação
        recent_actions = ModerationAction.objects.filter(
            created_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).select_related('comment')
        
        avg_moderation_time = None
        if recent_actions.exists():
            total_time = sum([
                (action.created_at - action.comment.created_at).total_seconds()
                for action in recent_actions
            ])
            avg_moderation_time = total_time / recent_actions.count() / 3600  # em horas
        
        return {
            'total_pending': total_pending,
            'by_priority': {item['priority']: item['count'] for item in by_priority},
            'assigned': assigned_count,
            'unassigned': unassigned_count,
            'avg_moderation_time_hours': avg_moderation_time,
        }
    
    def get_auto_moderation_stats(self, period_days: int = 30) -> Dict[str, int]:
        """Retorna estatísticas de moderação automática"""
        since = timezone.now() - timezone.timedelta(days=period_days)
        
        total_comments = Comment.objects.filter(
            created_at__gte=since
        ).count()
        
        auto_approved = Comment.objects.filter(
            created_at__gte=since,
            status='approved',
            moderated_by__isnull=True
        ).count()
        
        auto_rejected = Comment.objects.filter(
            created_at__gte=since,
            status__in=['rejected', 'spam'],
            moderated_by__isnull=True
        ).count()
        
        manual_moderated = Comment.objects.filter(
            created_at__gte=since,
            moderated_by__isnull=False
        ).count()
        
        return {
            'total_comments': total_comments,
            'auto_approved': auto_approved,
            'auto_rejected': auto_rejected,
            'manual_moderated': manual_moderated,
            'auto_moderation_rate': (auto_approved + auto_rejected) / total_comments * 100 if total_comments > 0 else 0,
        }
    
    def cleanup_old_moderation_data(self, days: int = 90) -> Dict[str, int]:
        """Remove dados antigos de moderação"""
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        
        # Remove ações de moderação antigas
        deleted_actions, _ = ModerationAction.objects.filter(
            created_at__lt=cutoff_date
        ).delete()
        
        # Remove itens da fila para comentários já moderados
        deleted_queue, _ = ModerationQueue.objects.filter(
            comment__status__in=['approved', 'rejected', 'spam', 'deleted'],
            updated_at__lt=cutoff_date
        ).delete()
        
        return {
            'deleted_actions': deleted_actions,
            'deleted_queue_items': deleted_queue,
        }