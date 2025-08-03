from typing import List, Optional, Dict, Any
from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.urls import reverse
from django.contrib.sites.models import Site

from ..interfaces.services import INotificationService, IWebSocketService
from ..interfaces.repositories import INotificationRepository
from ..models import Comment, CommentNotification, NotificationPreference

User = get_user_model()


class NotificationService(INotificationService):
    """
    Serviço de notificações de comentários
    
    Implementa INotificationService seguindo os princípios SOLID:
    - Single Responsibility: Apenas lógica de notificações
    - Open/Closed: Extensível via herança
    - Liskov Substitution: Pode substituir INotificationService
    - Interface Segregation: Interface específica para notificações
    - Dependency Inversion: Depende de abstrações (interfaces)
    """
    
    def __init__(self, notification_repository: INotificationRepository, websocket_service: Optional[IWebSocketService] = None):
        self.notification_repository = notification_repository
        self.websocket_service = websocket_service
    
    @transaction.atomic
    def create_reply_notification(self, comment: Comment, parent_comment: Comment) -> Optional[CommentNotification]:
        """Cria notificação de resposta"""
        # Não notifica se é resposta para si mesmo
        if comment.author == parent_comment.author:
            return None
        
        # Verifica preferências do usuário
        if not self._should_notify_user(parent_comment.author, 'reply'):
            return None
        
        notification = self.notification_repository.create(
            recipient=parent_comment.author,
            sender=comment.author,
            comment=comment,
            notification_type='reply',
            title=f'{comment.author.get_full_name() or comment.author.username} respondeu seu comentário',
            message=self._truncate_content(comment.content, 150)
        )
        
        # Envia notificação em tempo real
        self._send_realtime_notification(notification)
        
        # Agenda envio por email se habilitado
        if self._should_send_email(parent_comment.author, 'reply'):
            self._schedule_email_notification(notification)
        
        return notification
    
    @transaction.atomic
    def create_mention_notification(self, comment: Comment, mentioned_user: User) -> Optional[CommentNotification]:
        """Cria notificação de menção"""
        # Não notifica se mencionou a si mesmo
        if comment.author == mentioned_user:
            return None
        
        # Verifica preferências do usuário
        if not self._should_notify_user(mentioned_user, 'mention'):
            return None
        
        notification = self.notification_repository.create(
            recipient=mentioned_user,
            sender=comment.author,
            comment=comment,
            notification_type='mention',
            title=f'{comment.author.get_full_name() or comment.author.username} mencionou você',
            message=self._truncate_content(comment.content, 150)
        )
        
        # Envia notificação em tempo real
        self._send_realtime_notification(notification)
        
        # Agenda envio por email se habilitado
        if self._should_send_email(mentioned_user, 'mention'):
            self._schedule_email_notification(notification)
        
        return notification
    
    @transaction.atomic
    def create_like_notification(self, comment: Comment, liker: User) -> Optional[CommentNotification]:
        """Cria notificação de curtida"""
        # Não notifica se curtiu próprio comentário
        if comment.author == liker:
            return None
        
        # Verifica preferências do usuário
        if not self._should_notify_user(comment.author, 'like'):
            return None
        
        # Agrupa curtidas recentes para evitar spam
        recent_like_notifications = self.notification_repository.get_by_recipient(
            comment.author
        ).filter(
            notification_type='like',
            comment=comment,
            created_at__gte=timezone.now() - timezone.timedelta(hours=1),
            is_read=False
        )
        
        if recent_like_notifications.exists():
            # Atualiza notificação existente
            notification = recent_like_notifications.first()
            notification.message = f'{notification.message} e outros curtiram seu comentário'
            notification.save()
            return notification
        
        notification = self.notification_repository.create(
            recipient=comment.author,
            sender=liker,
            comment=comment,
            notification_type='like',
            title=f'{liker.get_full_name() or liker.username} curtiu seu comentário',
            message=self._truncate_content(comment.content, 100)
        )
        
        # Envia notificação em tempo real
        self._send_realtime_notification(notification)
        
        return notification
    
    @transaction.atomic
    def create_moderation_notification(self, comment: Comment, action: str, moderator: Optional[User] = None, reason: str = '') -> Optional[CommentNotification]:
        """Cria notificação de moderação"""
        # Verifica preferências do usuário
        if not self._should_notify_user(comment.author, 'moderation'):
            return None
        
        action_messages = {
            'approved': 'Seu comentário foi aprovado',
            'rejected': 'Seu comentário foi rejeitado',
            'spam': 'Seu comentário foi marcado como spam'
        }
        
        title = action_messages.get(action, f'Ação de moderação: {action}')
        message = self._truncate_content(comment.content, 100)
        
        if reason:
            message += f'\nMotivo: {reason}'
        
        notification = self.notification_repository.create(
            recipient=comment.author,
            sender=moderator,
            comment=comment,
            notification_type='moderation',
            title=title,
            message=message
        )
        
        # Envia notificação em tempo real
        self._send_realtime_notification(notification)
        
        # Sempre envia email para moderação
        self._schedule_email_notification(notification)
        
        return notification
    
    def get_user_notifications(self, user: User, unread_only: bool = False, limit: int = 50) -> QuerySet:
        """Busca notificações do usuário"""
        notifications = self.notification_repository.get_by_recipient(user)
        
        if unread_only:
            notifications = notifications.filter(is_read=False)
        
        return notifications[:limit]
    
    def get_unread_count(self, user: User) -> int:
        """Conta notificações não lidas"""
        return self.notification_repository.get_unread_count(user)
    
    @transaction.atomic
    def mark_as_read(self, notification_id: int, user: User) -> bool:
        """Marca notificação como lida"""
        notification = self.notification_repository.get_by_id(notification_id)
        
        if not notification or notification.recipient != user:
            return False
        
        return self.notification_repository.mark_as_read(notification)
    
    @transaction.atomic
    def mark_all_as_read(self, user: User) -> int:
        """Marca todas as notificações como lidas"""
        return self.notification_repository.mark_all_as_read(user)
    
    @transaction.atomic
    def delete_notification(self, notification_id: int, user: User) -> bool:
        """Remove notificação"""
        notification = self.notification_repository.get_by_id(notification_id)
        
        if not notification or notification.recipient != user:
            return False
        
        return self.notification_repository.delete(notification)
    
    def send_email_notification(self, notification: CommentNotification) -> bool:
        """Envia notificação por email"""
        if not notification.recipient.email:
            return False
        
        # Verifica se já foi enviado
        if notification.email_sent:
            return True
        
        try:
            # Prepara contexto do template
            context = {
                'notification': notification,
                'recipient': notification.recipient,
                'sender': notification.sender,
                'comment': notification.comment,
                'site': Site.objects.get_current(),
                'comment_url': self._get_comment_url(notification.comment),
                'unsubscribe_url': self._get_unsubscribe_url(notification.recipient),
            }
            
            # Renderiza template
            subject = f'[{Site.objects.get_current().name}] {notification.title}'
            html_message = render_to_string('comments/emails/notification.html', context)
            plain_message = strip_tags(html_message)
            
            # Envia email
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notification.recipient.email],
                html_message=html_message,
                fail_silently=False
            )
            
            # Marca como enviado
            notification.email_sent = True
            notification.email_sent_at = timezone.now()
            notification.save()
            
            return True
            
        except Exception as e:
            # Log do erro (em produção, usar logging)
            print(f'Erro ao enviar email: {e}')
            return False
    
    def get_notification_preferences(self, user: User) -> NotificationPreference:
        """Busca preferências de notificação do usuário"""
        preferences, created = NotificationPreference.objects.get_or_create(
            user=user,
            defaults={
                'email_replies': True,
                'email_mentions': True,
                'email_likes': False,
                'email_moderation': True,
                'realtime_replies': True,
                'realtime_mentions': True,
                'realtime_likes': True,
                'realtime_moderation': True,
                'email_frequency': 'immediate',
            }
        )
        return preferences
    
    @transaction.atomic
    def update_notification_preferences(self, user: User, **preferences) -> NotificationPreference:
        """Atualiza preferências de notificação"""
        user_preferences = self.get_notification_preferences(user)
        
        for key, value in preferences.items():
            if hasattr(user_preferences, key):
                setattr(user_preferences, key, value)
        
        user_preferences.save()
        return user_preferences
    
    def send_digest_email(self, user: User, notifications: List[CommentNotification]) -> bool:
        """Envia email de resumo"""
        if not notifications or not user.email:
            return False
        
        try:
            context = {
                'user': user,
                'notifications': notifications,
                'site': Site.objects.get_current(),
                'unsubscribe_url': self._get_unsubscribe_url(user),
            }
            
            subject = f'[{Site.objects.get_current().name}] Resumo de notificações'
            html_message = render_to_string('comments/emails/digest.html', context)
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False
            )
            
            # Marca notificações como enviadas
            for notification in notifications:
                notification.email_sent = True
                notification.email_sent_at = timezone.now()
                notification.save()
            
            return True
            
        except Exception as e:
            print(f'Erro ao enviar digest: {e}')
            return False
    
    def get_digest_notifications(self, user: User, frequency: str) -> List[CommentNotification]:
        """Busca notificações para digest"""
        preferences = self.get_notification_preferences(user)
        
        if frequency != preferences.email_frequency:
            return []
        
        # Define período baseado na frequência
        if frequency == 'daily':
            since = timezone.now() - timezone.timedelta(days=1)
        elif frequency == 'weekly':
            since = timezone.now() - timezone.timedelta(weeks=1)
        else:
            return []  # immediate não usa digest
        
        return list(
            self.notification_repository.get_for_digest(user, since)
        )
    
    def cleanup_old_notifications(self, days: int = 90) -> int:
        """Remove notificações antigas"""
        return self.notification_repository.delete_old_notifications(days)
    
    def get_notification_stats(self, user: User, days: int = 30) -> Dict[str, Any]:
        """Busca estatísticas de notificações"""
        return self.notification_repository.get_user_notification_stats(user, days)
    
    def _should_notify_user(self, user: User, notification_type: str) -> bool:
        """Verifica se deve notificar usuário"""
        preferences = self.get_notification_preferences(user)
        
        # Verifica horário de silêncio
        if preferences.quiet_hours_start and preferences.quiet_hours_end:
            current_time = timezone.now().time()
            if preferences.quiet_hours_start <= current_time <= preferences.quiet_hours_end:
                return False
        
        # Verifica preferência específica
        realtime_field = f'realtime_{notification_type}'
        if hasattr(preferences, realtime_field):
            return getattr(preferences, realtime_field)
        
        return True
    
    def _should_send_email(self, user: User, notification_type: str) -> bool:
        """Verifica se deve enviar email"""
        preferences = self.get_notification_preferences(user)
        
        # Verifica se email está habilitado para este tipo
        email_field = f'email_{notification_type}'
        if hasattr(preferences, email_field):
            enabled = getattr(preferences, email_field)
            if not enabled:
                return False
        
        # Verifica frequência
        return preferences.email_frequency == 'immediate'
    
    def _send_realtime_notification(self, notification: CommentNotification) -> None:
        """Envia notificação em tempo real via WebSocket"""
        if not self.websocket_service:
            return
        
        try:
            self.websocket_service.send_to_user(
                user=notification.recipient,
                message_type='notification',
                data={
                    'id': notification.id,
                    'type': notification.notification_type,
                    'title': notification.title,
                    'message': notification.message,
                    'sender': {
                        'id': notification.sender.id if notification.sender else None,
                        'username': notification.sender.username if notification.sender else 'Sistema',
                        'name': notification.sender.get_full_name() if notification.sender else 'Sistema',
                    },
                    'comment_id': notification.comment.id if notification.comment else None,
                    'created_at': notification.created_at.isoformat(),
                    'url': self._get_comment_url(notification.comment) if notification.comment else None,
                }
            )
        except Exception as e:
            print(f'Erro ao enviar notificação em tempo real: {e}')
    
    def _schedule_email_notification(self, notification: CommentNotification) -> None:
        """Agenda envio de email (implementação básica)"""
        # Em produção, usaria Celery ou similar
        # Por enquanto, envia imediatamente
        self.send_email_notification(notification)
    
    def _truncate_content(self, content: str, max_length: int) -> str:
        """Trunca conteúdo para notificação"""
        if len(content) <= max_length:
            return content
        
        return content[:max_length - 3] + '...'
    
    def _get_comment_url(self, comment: Comment) -> str:
        """Gera URL do comentário"""
        try:
            # Tenta gerar URL baseada no objeto do comentário
            if hasattr(comment.content_object, 'get_absolute_url'):
                base_url = comment.content_object.get_absolute_url()
                return f'{base_url}#comment-{comment.id}'
            
            # URL genérica
            return reverse('comments:detail', kwargs={'uuid': comment.uuid})
        except:
            return '/'
    
    def _get_unsubscribe_url(self, user: User) -> str:
        """Gera URL para cancelar inscrição"""
        try:
            return reverse('comments:unsubscribe', kwargs={'user_id': user.id})
        except:
            return '/'
    
    def process_pending_emails(self) -> int:
        """Processa emails pendentes"""
        pending_notifications = self.notification_repository.get_pending_emails()
        sent_count = 0
        
        for notification in pending_notifications[:100]:  # Processa até 100 por vez
            if self.send_email_notification(notification):
                sent_count += 1
        
        return sent_count
    
    def send_daily_digests(self) -> int:
        """Envia resumos diários"""
        users_with_daily = NotificationPreference.objects.filter(
            email_frequency='daily'
        ).select_related('user')
        
        sent_count = 0
        
        for preference in users_with_daily:
            notifications = self.get_digest_notifications(preference.user, 'daily')
            if notifications and self.send_digest_email(preference.user, notifications):
                sent_count += 1
        
        return sent_count
    
    def send_weekly_digests(self) -> int:
        """Envia resumos semanais"""
        users_with_weekly = NotificationPreference.objects.filter(
            email_frequency='weekly'
        ).select_related('user')
        
        sent_count = 0
        
        for preference in users_with_weekly:
            notifications = self.get_digest_notifications(preference.user, 'weekly')
            if notifications and self.send_digest_email(preference.user, notifications):
                sent_count += 1
        
        return sent_count