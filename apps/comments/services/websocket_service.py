from typing import Dict, Any, List, Optional
from django.contrib.auth import get_user_model
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.serializers.json import DjangoJSONEncoder
import json
import logging

from ..interfaces.services import IWebSocketService
from ..models import Comment

User = get_user_model()
logger = logging.getLogger(__name__)


class WebSocketService(IWebSocketService):
    """
    Serviço WebSocket para comunicação em tempo real
    
    Implementa IWebSocketService seguindo os princípios SOLID:
    - Single Responsibility: Apenas comunicação WebSocket
    - Open/Closed: Extensível via herança
    - Liskov Substitution: Pode substituir IWebSocketService
    - Interface Segregation: Interface específica para WebSocket
    - Dependency Inversion: Depende de abstrações (interfaces)
    """
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
    
    def send_to_user(self, user: User, message_type: str, data: Dict[str, Any]) -> bool:
        """Envia mensagem para usuário específico"""
        if not self.channel_layer:
            logger.warning('Channel layer não configurado')
            return False
        
        try:
            group_name = f'user_{user.id}'
            message = {
                'type': 'send_message',
                'message_type': message_type,
                'data': data,
                'timestamp': self._get_timestamp()
            }
            
            async_to_sync(self.channel_layer.group_send)(
                group_name,
                message
            )
            
            logger.info(f'Mensagem enviada para usuário {user.id}: {message_type}')
            return True
            
        except Exception as e:
            logger.error(f'Erro ao enviar mensagem para usuário {user.id}: {e}')
            return False
    
    def send_to_group(self, group_name: str, message_type: str, data: Dict[str, Any]) -> bool:
        """Envia mensagem para grupo"""
        if not self.channel_layer:
            logger.warning('Channel layer não configurado')
            return False
        
        try:
            message = {
                'type': 'send_message',
                'message_type': message_type,
                'data': data,
                'timestamp': self._get_timestamp()
            }
            
            async_to_sync(self.channel_layer.group_send)(
                group_name,
                message
            )
            
            logger.info(f'Mensagem enviada para grupo {group_name}: {message_type}')
            return True
            
        except Exception as e:
            logger.error(f'Erro ao enviar mensagem para grupo {group_name}: {e}')
            return False
    
    def broadcast_comment_update(self, comment: Comment, action: str, user: Optional[User] = None) -> bool:
        """Transmite atualização de comentário"""
        try:
            # Grupo baseado no objeto do comentário
            content_type = comment.content_type
            object_id = comment.object_id
            group_name = f'comments_{content_type.app_label}_{content_type.model}_{object_id}'
            
            data = {
                'action': action,
                'comment': self._serialize_comment(comment),
                'user': self._serialize_user(user) if user else None,
            }
            
            return self.send_to_group(group_name, 'comment_update', data)
            
        except Exception as e:
            logger.error(f'Erro ao transmitir atualização de comentário {comment.id}: {e}')
            return False
    
    def broadcast_reaction_update(self, comment: Comment, reaction_data: Dict[str, Any], user: User) -> bool:
        """Transmite atualização de reação"""
        try:
            content_type = comment.content_type
            object_id = comment.object_id
            group_name = f'comments_{content_type.app_label}_{content_type.model}_{object_id}'
            
            data = {
                'comment_id': comment.id,
                'comment_uuid': str(comment.uuid),
                'reaction_data': reaction_data,
                'user': self._serialize_user(user),
            }
            
            return self.send_to_group(group_name, 'reaction_update', data)
            
        except Exception as e:
            logger.error(f'Erro ao transmitir reação do comentário {comment.id}: {e}')
            return False
    
    def broadcast_moderation_update(self, comment: Comment, action: str, moderator: Optional[User] = None) -> bool:
        """Transmite atualização de moderação"""
        try:
            # Envia para o autor do comentário
            if comment.author:
                author_data = {
                    'comment_id': comment.id,
                    'comment_uuid': str(comment.uuid),
                    'action': action,
                    'new_status': comment.status,
                    'moderator': self._serialize_user(moderator) if moderator else {'username': 'Sistema'},
                }
                
                self.send_to_user(comment.author, 'moderation_update', author_data)
            
            # Envia para o grupo de comentários (para atualizar visualização)
            content_type = comment.content_type
            object_id = comment.object_id
            group_name = f'comments_{content_type.app_label}_{content_type.model}_{object_id}'
            
            group_data = {
                'comment_id': comment.id,
                'comment_uuid': str(comment.uuid),
                'action': action,
                'new_status': comment.status,
            }
            
            return self.send_to_group(group_name, 'comment_moderated', group_data)
            
        except Exception as e:
            logger.error(f'Erro ao transmitir moderação do comentário {comment.id}: {e}')
            return False
    
    def join_comment_room(self, user: User, content_object: Any) -> str:
        """Adiciona usuário ao grupo de comentários"""
        try:
            from django.contrib.contenttypes.models import ContentType
            content_type = ContentType.objects.get_for_model(content_object)
            group_name = f'comments_{content_type.app_label}_{content_type.model}_{content_object.id}'
            
            # Em implementação real, isso seria feito no consumer WebSocket
            # Aqui apenas retornamos o nome do grupo
            return group_name
            
        except Exception as e:
            logger.error(f'Erro ao entrar no grupo de comentários: {e}')
            return ''
    
    def leave_comment_room(self, user: User, content_object: Any) -> bool:
        """Remove usuário do grupo de comentários"""
        try:
            # Em implementação real, isso seria feito no consumer WebSocket
            return True
            
        except Exception as e:
            logger.error(f'Erro ao sair do grupo de comentários: {e}')
            return False
    
    def send_typing_indicator(self, user: User, content_object: Any, is_typing: bool) -> bool:
        """Envia indicador de digitação"""
        try:
            from django.contrib.contenttypes.models import ContentType
            content_type = ContentType.objects.get_for_model(content_object)
            group_name = f'comments_{content_type.app_label}_{content_type.model}_{content_object.id}'
            
            data = {
                'user': self._serialize_user(user),
                'is_typing': is_typing,
            }
            
            return self.send_to_group(group_name, 'typing_indicator', data)
            
        except Exception as e:
            logger.error(f'Erro ao enviar indicador de digitação: {e}')
            return False
    
    def send_user_count_update(self, content_object: Any, user_count: int) -> bool:
        """Envia atualização de contagem de usuários online"""
        try:
            from django.contrib.contenttypes.models import ContentType
            content_type = ContentType.objects.get_for_model(content_object)
            group_name = f'comments_{content_type.app_label}_{content_type.model}_{content_object.id}'
            
            data = {
                'user_count': user_count,
            }
            
            return self.send_to_group(group_name, 'user_count_update', data)
            
        except Exception as e:
            logger.error(f'Erro ao enviar contagem de usuários: {e}')
            return False
    
    def send_notification_count_update(self, user: User, unread_count: int) -> bool:
        """Envia atualização de contagem de notificações"""
        try:
            data = {
                'unread_count': unread_count,
            }
            
            return self.send_to_user(user, 'notification_count_update', data)
            
        except Exception as e:
            logger.error(f'Erro ao enviar contagem de notificações para usuário {user.id}: {e}')
            return False
    
    def broadcast_system_message(self, message: str, message_type: str = 'info') -> bool:
        """Transmite mensagem do sistema para todos"""
        try:
            data = {
                'message': message,
                'type': message_type,
            }
            
            return self.send_to_group('system_messages', 'system_message', data)
            
        except Exception as e:
            logger.error(f'Erro ao transmitir mensagem do sistema: {e}')
            return False
    
    def send_comment_thread_update(self, root_comment: Comment, action: str, affected_comment: Comment) -> bool:
        """Envia atualização de thread de comentários"""
        try:
            content_type = root_comment.content_type
            object_id = root_comment.object_id
            group_name = f'comments_{content_type.app_label}_{content_type.model}_{object_id}'
            
            data = {
                'action': action,
                'root_comment_id': root_comment.id,
                'affected_comment': self._serialize_comment(affected_comment),
                'thread_stats': {
                    'total_replies': root_comment.replies_count,
                    'depth': affected_comment.depth,
                }
            }
            
            return self.send_to_group(group_name, 'thread_update', data)
            
        except Exception as e:
            logger.error(f'Erro ao enviar atualização de thread: {e}')
            return False
    
    def _serialize_comment(self, comment: Comment) -> Dict[str, Any]:
        """Serializa comentário para WebSocket"""
        return {
            'id': comment.id,
            'uuid': str(comment.uuid),
            'content': comment.content,
            'author': self._serialize_user(comment.author),
            'status': comment.status,
            'created_at': comment.created_at.isoformat(),
            'updated_at': comment.updated_at.isoformat(),
            'is_edited': comment.is_edited,
            'is_pinned': comment.is_pinned,
            'likes_count': comment.likes_count,
            'dislikes_count': comment.dislikes_count,
            'replies_count': comment.replies_count,
            'depth': comment.depth,
            'parent_id': comment.parent_id,
        }
    
    def _serialize_user(self, user: User) -> Dict[str, Any]:
        """Serializa usuário para WebSocket"""
        if not user:
            return {'username': 'Anônimo', 'id': None}
        
        return {
            'id': user.id,
            'username': user.username,
            'name': user.get_full_name() or user.username,
            'is_staff': user.is_staff,
            'avatar_url': getattr(user, 'avatar_url', None) or '/static/images/default-avatar.png',
        }
    
    def _get_timestamp(self) -> str:
        """Retorna timestamp atual"""
        from django.utils import timezone
        return timezone.now().isoformat()
    
    def get_active_users_count(self, content_object: Any) -> int:
        """Retorna contagem de usuários ativos (implementação básica)"""
        # Em implementação real, manteria contagem em cache/Redis
        # Por enquanto, retorna valor fixo
        return 0
    
    def is_user_online(self, user: User) -> bool:
        """Verifica se usuário está online"""
        # Em implementação real, verificaria conexões ativas
        return False
    
    def send_bulk_notification(self, users: List[User], message_type: str, data: Dict[str, Any]) -> int:
        """Envia notificação para múltiplos usuários"""
        sent_count = 0
        
        for user in users:
            if self.send_to_user(user, message_type, data):
                sent_count += 1
        
        return sent_count
    
    def create_private_room(self, users: List[User]) -> str:
        """Cria sala privada para usuários"""
        # Gera nome único para a sala
        user_ids = sorted([user.id for user in users])
        room_name = f'private_{"_".join(map(str, user_ids))}'
        
        return room_name
    
    def send_to_moderators(self, message_type: str, data: Dict[str, Any]) -> bool:
        """Envia mensagem para todos os moderadores"""
        try:
            return self.send_to_group('moderators', message_type, data)
        except Exception as e:
            logger.error(f'Erro ao enviar mensagem para moderadores: {e}')
            return False
    
    def send_moderation_alert(self, comment: Comment, alert_type: str, details: Dict[str, Any]) -> bool:
        """Envia alerta de moderação"""
        try:
            data = {
                'alert_type': alert_type,
                'comment': self._serialize_comment(comment),
                'details': details,
                'priority': details.get('priority', 'normal'),
            }
            
            return self.send_to_moderators('moderation_alert', data)
            
        except Exception as e:
            logger.error(f'Erro ao enviar alerta de moderação: {e}')
            return False
    
    def send_spam_detection_alert(self, comment: Comment, spam_score: float, indicators: List[str]) -> bool:
        """Envia alerta de detecção de spam"""
        try:
            details = {
                'spam_score': spam_score,
                'indicators': indicators,
                'priority': 'high' if spam_score > 0.8 else 'normal',
            }
            
            return self.send_moderation_alert(comment, 'spam_detected', details)
            
        except Exception as e:
            logger.error(f'Erro ao enviar alerta de spam: {e}')
            return False
    
    def send_report_alert(self, comment: Comment, reporter: User, reason: str) -> bool:
        """Envia alerta de report"""
        try:
            details = {
                'reporter': self._serialize_user(reporter),
                'reason': reason,
                'priority': 'high',
            }
            
            return self.send_moderation_alert(comment, 'comment_reported', details)
            
        except Exception as e:
            logger.error(f'Erro ao enviar alerta de report: {e}')
            return False
    
    def cleanup_inactive_connections(self) -> int:
        """Remove conexões inativas (implementação básica)"""
        # Em implementação real, limparia conexões WebSocket inativas
        return 0
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de conexões"""
        # Em implementação real, retornaria estatísticas reais
        return {
            'total_connections': 0,
            'active_users': 0,
            'active_rooms': 0,
            'messages_sent_today': 0,
        }