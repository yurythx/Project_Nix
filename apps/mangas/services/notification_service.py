"""
Serviço para gerenciar notificações push e do sistema.
"""

import logging
import json
import requests
from typing import List, Dict, Any, Optional
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings

from ..models.notifications import Notification, PushSubscription, NotificationPreference, NotificationTemplate
from ..models.comments import ChapterComment
from ..models.capitulo import Capitulo

logger = logging.getLogger(__name__)
User = get_user_model()

class NotificationService:
    """
    Serviço para gerenciar notificações do sistema.
    """
    
    def __init__(self):
        self.cache_timeout = 300  # 5 minutos
        self.batch_size = 100  # Tamanho do lote para envio
    
    def send_notification(self, recipient: User, notification_type: str, title: str, 
                         message: str, data: Dict[str, Any] = None, priority: str = 'normal') -> Notification:
        """
        Envia uma notificação para um usuário.
        """
        # Verificar preferências do usuário
        preferences = self._get_user_preferences(recipient)
        
        # Verificar se o tipo de notificação está habilitado
        if not self._is_notification_enabled(preferences, notification_type):
            return None
        
        # Verificar horário silencioso
        if preferences.is_in_quiet_hours:
            logger.info(f"Notificação silenciada para {recipient.username} (horário silencioso)")
            return None
        
        # Criar notificação
        notification = Notification.objects.create(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            message=message,
            data=data or {},
            priority=priority
        )
        
        # Enviar notificações em background
        self._send_notifications_async([notification])
        
        return notification
    
    def send_comment_reply_notification(self, comment: ChapterComment, reply: ChapterComment):
        """
        Envia notificação de resposta a comentário.
        """
        if comment.user == reply.user:
            return  # Não notificar o próprio autor
        
        title = f"Resposta ao seu comentário"
        message = f"{reply.user.username} respondeu ao seu comentário no capítulo {comment.capitulo.number}"
        
        data = {
            'comment_id': comment.id,
            'reply_id': reply.id,
            'chapter_id': comment.capitulo.id,
            'manga_id': comment.capitulo.manga.id,
            'manga_title': comment.capitulo.manga.title,
            'chapter_number': comment.capitulo.number,
        }
        
        return self.send_notification(
            recipient=comment.user,
            notification_type='comment_reply',
            title=title,
            message=message,
            data=data
        )
    
    def send_comment_reaction_notification(self, comment: ChapterComment, reaction_type: str, user: User):
        """
        Envia notificação de reação a comentário.
        """
        if comment.user == user:
            return  # Não notificar o próprio autor
        
        reaction_names = {
            'like': 'curtiu',
            'love': 'amou',
            'laugh': 'riu de',
            'wow': 'ficou surpreso com',
            'sad': 'ficou triste com',
            'angry': 'ficou bravo com',
        }
        
        action = reaction_names.get(reaction_type, 'reagiu a')
        title = f"Reação ao seu comentário"
        message = f"{user.username} {action} seu comentário no capítulo {comment.capitulo.number}"
        
        data = {
            'comment_id': comment.id,
            'reaction_type': reaction_type,
            'chapter_id': comment.capitulo.id,
            'manga_id': comment.capitulo.manga.id,
            'manga_title': comment.capitulo.manga.title,
            'chapter_number': comment.capitulo.number,
        }
        
        return self.send_notification(
            recipient=comment.user,
            notification_type='comment_reaction',
            title=title,
            message=message,
            data=data
        )
    
    def send_new_chapter_notification(self, capitulo: Capitulo, followers: List[User]):
        """
        Envia notificação de novo capítulo para seguidores.
        """
        title = f"Novo capítulo disponível!"
        message = f"Capítulo {capitulo.number} de {capitulo.manga.title} foi publicado"
        
        data = {
            'chapter_id': capitulo.id,
            'manga_id': capitulo.manga.id,
            'manga_title': capitulo.manga.title,
            'chapter_number': capitulo.number,
            'chapter_title': capitulo.title,
        }
        
        notifications = []
        for follower in followers:
            notification = self.send_notification(
                recipient=follower,
                notification_type='new_chapter',
                title=title,
                message=message,
                data=data,
                priority='high'
            )
            if notification:
                notifications.append(notification)
        
        return notifications
    
    def send_download_complete_notification(self, user: User, capitulo: Capitulo, file_size: int):
        """
        Envia notificação de download concluído.
        """
        title = f"Download concluído!"
        message = f"Capítulo {capitulo.number} de {capitulo.manga.title} foi baixado com sucesso"
        
        data = {
            'chapter_id': capitulo.id,
            'manga_id': capitulo.manga.id,
            'manga_title': capitulo.manga.title,
            'chapter_number': capitulo.number,
            'file_size': file_size,
        }
        
        return self.send_notification(
            recipient=user,
            notification_type='download_complete',
            title=title,
            message=message,
            data=data
        )
    
    def send_mention_notification(self, comment: ChapterComment, mentioned_users: List[User]):
        """
        Envia notificação de menção em comentário.
        """
        title = f"Você foi mencionado!"
        message = f"{comment.user.username} mencionou você em um comentário"
        
        data = {
            'comment_id': comment.id,
            'chapter_id': comment.capitulo.id,
            'manga_id': comment.capitulo.manga.id,
            'manga_title': comment.capitulo.manga.title,
            'chapter_number': comment.capitulo.number,
        }
        
        notifications = []
        for user in mentioned_users:
            if user != comment.user:  # Não notificar o próprio autor
                notification = self.send_notification(
                    recipient=user,
                    notification_type='comment_mention',
                    title=title,
                    message=message,
                    data=data
                )
                if notification:
                    notifications.append(notification)
        
        return notifications
    
    def register_push_subscription(self, user: User, endpoint: str, p256dh_key: str, 
                                  auth_token: str, device_info: Dict[str, Any] = None) -> PushSubscription:
        """
        Registra uma assinatura push para um usuário.
        """
        subscription, created = PushSubscription.objects.get_or_create(
            user=user,
            endpoint=endpoint,
            defaults={
                'p256dh_key': p256dh_key,
                'auth_token': auth_token,
                'device_info': device_info or {},
            }
        )
        
        if not created:
            # Atualizar dados existentes
            subscription.p256dh_key = p256dh_key
            subscription.auth_token = auth_token
            subscription.device_info = device_info or {}
            subscription.save()
        
        return subscription
    
    def unregister_push_subscription(self, user: User, endpoint: str) -> bool:
        """
        Remove uma assinatura push.
        """
        try:
            subscription = PushSubscription.objects.get(user=user, endpoint=endpoint)
            subscription.delete()
            return True
        except PushSubscription.DoesNotExist:
            return False
    
    def get_user_notifications(self, user: User, page: int = 1, limit: int = 20) -> Dict[str, Any]:
        """
        Obtém notificações de um usuário com paginação.
        """
        notifications = Notification.objects.filter(
            recipient=user
        ).order_by('-created_at')
        
        total = notifications.count()
        start = (page - 1) * limit
        end = start + limit
        
        page_notifications = notifications[start:end]
        
        return {
            'notifications': page_notifications,
            'total': total,
            'page': page,
            'has_next': end < total,
            'has_previous': page > 1,
        }
    
    def mark_notification_as_read(self, notification_id: int, user: User) -> bool:
        """
        Marca uma notificação como lida.
        """
        try:
            notification = Notification.objects.get(id=notification_id, recipient=user)
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            return False
    
    def mark_all_notifications_as_read(self, user: User) -> int:
        """
        Marca todas as notificações do usuário como lidas.
        """
        count = Notification.objects.filter(
            recipient=user,
            is_read=False
        ).update(is_read=True)
        
        return count
    
    def get_unread_count(self, user: User) -> int:
        """
        Obtém o número de notificações não lidas.
        """
        cache_key = f'unread_notifications_{user.id}'
        count = cache.get(cache_key)
        
        if count is None:
            count = Notification.objects.filter(
                recipient=user,
                is_read=False
            ).count()
            cache.set(cache_key, count, self.cache_timeout)
        
        return count
    
    def cleanup_expired_notifications(self) -> int:
        """
        Remove notificações expiradas.
        """
        expired = Notification.objects.filter(
            expires_at__lt=timezone.now()
        )
        count = expired.count()
        expired.delete()
        
        logger.info(f"Removidas {count} notificações expiradas")
        return count
    
    def _send_notifications_async(self, notifications: List[Notification]):
        """
        Envia notificações em background.
        """
        # Em produção, use Celery ou similar
        for notification in notifications:
            try:
                self._send_push_notification(notification)
                self._send_email_notification(notification)
                notification.mark_as_sent()
            except Exception as e:
                logger.error(f"Erro ao enviar notificação {notification.id}: {str(e)}")
    
    def _send_push_notification(self, notification: Notification):
        """
        Envia notificação push.
        """
        preferences = self._get_user_preferences(notification.recipient)
        
        if not preferences.push_notifications:
            return
        
        subscriptions = PushSubscription.objects.filter(
            user=notification.recipient,
            is_active=True
        )
        
        for subscription in subscriptions:
            try:
                self._send_web_push_notification(subscription, notification)
            except Exception as e:
                logger.error(f"Erro ao enviar push para {subscription.endpoint}: {str(e)}")
                # Marcar como inativa se falhar várias vezes
                subscription.is_active = False
                subscription.save()
    
    def _send_web_push_notification(self, subscription: PushSubscription, notification: Notification):
        """
        Envia notificação web push usando VAPID.
        """
        # Implementar envio usando pywebpush ou similar
        # Este é um exemplo básico
        payload = {
            'title': notification.title,
            'body': notification.message,
            'icon': '/static/images/notification-icon.png',
            'badge': '/static/images/badge-icon.png',
            'data': notification.data,
            'actions': [
                {
                    'action': 'view',
                    'title': 'Ver'
                },
                {
                    'action': 'dismiss',
                    'title': 'Fechar'
                }
            ]
        }
        
        # Aqui você usaria pywebpush para enviar
        # pywebpush(subscription_info, data, vapid_private_key, vapid_claims)
        pass
    
    def _send_email_notification(self, notification: Notification):
        """
        Envia notificação por email.
        """
        preferences = self._get_user_preferences(notification.recipient)
        
        if not preferences.email_notifications:
            return
        
        # Implementar envio de email
        # Usar Django's email backend ou serviço externo
        pass
    
    def _get_user_preferences(self, user: User) -> NotificationPreference:
        """
        Obtém ou cria preferências de notificação do usuário.
        """
        preferences, created = NotificationPreference.objects.get_or_create(
            user=user,
            defaults={
                'comment_replies': True,
                'comment_reactions': True,
                'new_chapters': True,
                'download_complete': True,
                'push_notifications': True,
                'email_notifications': True,
                'browser_notifications': True,
            }
        )
        return preferences
    
    def _is_notification_enabled(self, preferences: NotificationPreference, notification_type: str) -> bool:
        """
        Verifica se um tipo de notificação está habilitado.
        """
        type_mapping = {
            'comment_reply': preferences.comment_replies,
            'comment_reaction': preferences.comment_reactions,
            'new_chapter': preferences.new_chapters,
            'download_complete': preferences.download_complete,
            'moderation_action': preferences.moderation_actions,
            'system_announcement': preferences.system_announcements,
            'manga_follow': preferences.manga_follows,
            'comment_mention': preferences.comment_mentions,
        }
        
        return type_mapping.get(notification_type, True)
    
    def _extract_mentions(self, content: str) -> List[str]:
        """
        Extrai menções de usuários do conteúdo.
        """
        import re
        mentions = re.findall(r'@(\w+)', content)
        return list(set(mentions))  # Remove duplicatas
    
    def _get_mentioned_users(self, mentions: List[str]) -> List[User]:
        """
        Obtém usuários mencionados.
        """
        return User.objects.filter(username__in=mentions) 