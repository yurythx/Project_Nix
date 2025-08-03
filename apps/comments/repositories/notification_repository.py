from typing import List, Optional, Dict, Any
from django.contrib.auth import get_user_model
from django.db.models import QuerySet, Q, Count
from django.db import transaction
from django.utils import timezone

from ..interfaces.repositories import INotificationRepository
from ..models import CommentNotification, NotificationPreference

User = get_user_model()


class DjangoNotificationRepository(INotificationRepository):
    """
    Implementação Django do repositório de notificações
    
    Implementa INotificationRepository seguindo os princípios SOLID
    """
    
    def get_by_id(self, notification_id: int) -> Optional[CommentNotification]:
        """Busca notificação por ID"""
        try:
            return CommentNotification.objects.select_related(
                'recipient', 'sender', 'comment', 'content_type'
            ).get(id=notification_id)
        except CommentNotification.DoesNotExist:
            return None
    
    def get_by_uuid(self, uuid: str) -> Optional[CommentNotification]:
        """Busca notificação por UUID"""
        try:
            return CommentNotification.objects.select_related(
                'recipient', 'sender', 'comment', 'content_type'
            ).get(uuid=uuid)
        except CommentNotification.DoesNotExist:
            return None
    
    def get_for_user(self, user: User, is_read: Optional[bool] = None) -> QuerySet:
        """Busca notificações do usuário"""
        queryset = CommentNotification.objects.filter(
            recipient=user
        ).select_related(
            'sender', 'comment', 'content_type'
        )
        
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read)
        
        return queryset.order_by('-created_at')
    
    def get_unread_count(self, user: User) -> int:
        """Conta notificações não lidas"""
        return CommentNotification.objects.filter(
            recipient=user,
            is_read=False
        ).count()
    
    @transaction.atomic
    def create(self, **kwargs) -> CommentNotification:
        """Cria nova notificação"""
        return CommentNotification.objects.create(**kwargs)
    
    @transaction.atomic
    def mark_as_read(self, notification: CommentNotification) -> CommentNotification:
        """Marca notificação como lida"""
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=['is_read', 'read_at'])
        
        return notification
    
    @transaction.atomic
    def mark_all_as_read(self, user: User) -> int:
        """Marca todas as notificações como lidas"""
        updated = CommentNotification.objects.filter(
            recipient=user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return updated
    
    @transaction.atomic
    def delete_old_notifications(self, days: int = 30) -> int:
        """Remove notificações antigas"""
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        
        deleted, _ = CommentNotification.objects.filter(
            created_at__lt=cutoff_date,
            is_read=True
        ).delete()
        
        return deleted
    
    def get_pending_email_notifications(self) -> QuerySet:
        """Busca notificações pendentes de envio por email"""
        return CommentNotification.objects.filter(
            is_sent=False
        ).select_related(
            'recipient', 'sender', 'comment'
        ).order_by('created_at')
    
    @transaction.atomic
    def mark_as_sent(self, notification: CommentNotification) -> CommentNotification:
        """Marca notificação como enviada"""
        if not notification.is_sent:
            notification.is_sent = True
            notification.sent_at = timezone.now()
            notification.save(update_fields=['is_sent', 'sent_at'])
        
        return notification
    
    def get_user_preferences(self, user: User) -> NotificationPreference:
        """Busca preferências de notificação do usuário"""
        preferences, created = NotificationPreference.objects.get_or_create(
            user=user
        )
        return preferences
    
    @transaction.atomic
    def update_user_preferences(self, user: User, **kwargs) -> NotificationPreference:
        """Atualiza preferências de notificação"""
        preferences = self.get_user_preferences(user)
        
        for field, value in kwargs.items():
            if hasattr(preferences, field):
                setattr(preferences, field, value)
        
        preferences.save()
        return preferences
    
    def get_digest_notifications(self, user: User, frequency: str) -> QuerySet:
        """Busca notificações para resumo"""
        # Calcula período baseado na frequência
        now = timezone.now()
        
        if frequency == 'daily':
            since = now - timezone.timedelta(days=1)
        elif frequency == 'weekly':
            since = now - timezone.timedelta(weeks=1)
        elif frequency == 'monthly':
            since = now - timezone.timedelta(days=30)
        else:
            return CommentNotification.objects.none()
        
        return CommentNotification.objects.filter(
            recipient=user,
            created_at__gte=since,
            is_sent=False
        ).select_related(
            'sender', 'comment', 'content_type'
        ).order_by('-created_at')
    
    @transaction.atomic
    def bulk_create(self, notifications: List[Dict[str, Any]]) -> List[CommentNotification]:
        """Cria múltiplas notificações"""
        notification_objects = [
            CommentNotification(**notification_data)
            for notification_data in notifications
        ]
        
        return CommentNotification.objects.bulk_create(notification_objects)
    
    def get_notification_statistics(self, user: Optional[User] = None, period_days: int = 30) -> Dict[str, Any]:
        """Retorna estatísticas de notificações"""
        since = timezone.now() - timezone.timedelta(days=period_days)
        
        queryset = CommentNotification.objects.filter(
            created_at__gte=since
        )
        
        if user:
            queryset = queryset.filter(recipient=user)
        
        stats = queryset.aggregate(
            total=Count('id'),
            read=Count('id', filter=Q(is_read=True)),
            unread=Count('id', filter=Q(is_read=False)),
            sent=Count('id', filter=Q(is_sent=True)),
            pending=Count('id', filter=Q(is_sent=False)),
        )
        
        # Estatísticas por tipo
        by_type = queryset.values('notification_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        stats['by_type'] = {item['notification_type']: item['count'] for item in by_type}
        
        # Taxa de leitura
        if stats['total'] > 0:
            stats['read_rate'] = (stats['read'] / stats['total']) * 100
        else:
            stats['read_rate'] = 0
        
        return stats
    
    def get_most_active_senders(self, period_days: int = 30, limit: int = 10) -> QuerySet:
        """Busca usuários que mais geram notificações"""
        since = timezone.now() - timezone.timedelta(days=period_days)
        
        return User.objects.filter(
            sent_comment_notifications__created_at__gte=since
        ).annotate(
            notification_count=Count('sent_comment_notifications')
        ).order_by('-notification_count')[:limit]
    
    def get_notification_trends(self, period_days: int = 30) -> Dict[str, List[Dict[str, Any]]]:
        """Retorna tendências de notificações por dia"""
        since = timezone.now() - timezone.timedelta(days=period_days)
        
        # Agrupa por dia
        daily_stats = CommentNotification.objects.filter(
            created_at__gte=since
        ).extra(
            select={'day': 'DATE(created_at)'}
        ).values('day', 'notification_type').annotate(
            count=Count('id')
        ).order_by('day')
        
        # Organiza dados por tipo
        trends = {}
        for stat in daily_stats:
            notification_type = stat['notification_type']
            if notification_type not in trends:
                trends[notification_type] = []
            
            trends[notification_type].append({
                'date': stat['day'],
                'count': stat['count']
            })
        
        return trends
    
    def cleanup_duplicate_notifications(self) -> int:
        """Remove notificações duplicadas"""
        # Identifica duplicatas baseado em recipient, comment e notification_type
        duplicates = CommentNotification.objects.values(
            'recipient', 'comment', 'notification_type'
        ).annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        deleted_count = 0
        
        for duplicate in duplicates:
            # Mantém apenas a mais recente
            notifications = CommentNotification.objects.filter(
                recipient=duplicate['recipient'],
                comment=duplicate['comment'],
                notification_type=duplicate['notification_type']
            ).order_by('-created_at')
            
            # Remove todas exceto a primeira (mais recente)
            to_delete = notifications[1:]
            for notification in to_delete:
                notification.delete()
                deleted_count += 1
        
        return deleted_count
    
    def get_realtime_notifications(self, user: User, limit: int = 50) -> QuerySet:
        """Busca notificações para envio em tempo real"""
        return CommentNotification.objects.filter(
            recipient=user,
            is_real_time_sent=False,
            created_at__gte=timezone.now() - timezone.timedelta(minutes=5)
        ).select_related(
            'sender', 'comment'
        ).order_by('-created_at')[:limit]
    
    @transaction.atomic
    def mark_as_real_time_sent(self, notifications: List[CommentNotification]) -> int:
        """Marca notificações como enviadas em tempo real"""
        notification_ids = [n.id for n in notifications]
        
        updated = CommentNotification.objects.filter(
            id__in=notification_ids
        ).update(
            is_real_time_sent=True
        )
        
        return updated
    
    def get_user_notification_summary(self, user: User) -> Dict[str, Any]:
        """Retorna resumo de notificações do usuário"""
        total = CommentNotification.objects.filter(recipient=user).count()
        unread = self.get_unread_count(user)
        
        # Últimas notificações por tipo
        recent_by_type = {}
        for notification_type, _ in CommentNotification.NOTIFICATION_TYPES:
            recent = CommentNotification.objects.filter(
                recipient=user,
                notification_type=notification_type
            ).order_by('-created_at').first()
            
            if recent:
                recent_by_type[notification_type] = {
                    'last_received': recent.created_at,
                    'count_today': CommentNotification.objects.filter(
                        recipient=user,
                        notification_type=notification_type,
                        created_at__gte=timezone.now().replace(hour=0, minute=0, second=0)
                    ).count()
                }
        
        return {
            'total_notifications': total,
            'unread_count': unread,
            'read_rate': ((total - unread) / total * 100) if total > 0 else 0,
            'recent_by_type': recent_by_type,
        }