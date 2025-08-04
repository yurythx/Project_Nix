from typing import Dict, Any
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist

User = get_user_model()
logger = logging.getLogger(__name__)


class CommentConsumer(AsyncWebsocketConsumer):
    """
    Consumer WebSocket para comentários em tempo real
    
    Gerencia conexões WebSocket para:
    - Atualizações de comentários
    - Notificações em tempo real
    - Indicadores de digitação
    - Contagem de usuários online
    """
    
    async def connect(self):
        """Conecta usuário ao WebSocket"""
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Grupos do usuário
        self.user_group = f'user_{self.user.id}'
        self.comment_groups = set()
        
        # Adiciona ao grupo pessoal
        await self.channel_layer.group_add(
            self.user_group,
            self.channel_name
        )
        
        await self.accept()
        
        logger.info(f'Usuário {self.user.username} conectado ao WebSocket')
    
    async def disconnect(self, close_code):
        """Desconecta usuário do WebSocket"""
        # Remove de todos os grupos apenas se foram definidos
        if hasattr(self, 'user_group'):
            await self.channel_layer.group_discard(
                self.user_group,
                self.channel_name
            )
        
        if hasattr(self, 'comment_groups'):
            for group_name in self.comment_groups:
                await self.channel_layer.group_discard(
                    group_name,
                    self.channel_name
                )
        
        logger.info(f'Usuário {self.user.username} desconectado do WebSocket')
    
    async def receive(self, text_data):
        """Recebe mensagem do cliente"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'join_comment_room':
                await self.join_comment_room(data)
            elif message_type == 'leave_comment_room':
                await self.leave_comment_room(data)
            elif message_type == 'typing_indicator':
                await self.handle_typing_indicator(data)
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
            else:
                logger.warning(f'Tipo de mensagem desconhecido: {message_type}')
                
        except json.JSONDecodeError:
            logger.error('Erro ao decodificar JSON')
        except Exception as e:
            logger.error(f'Erro ao processar mensagem: {e}')
    
    async def join_comment_room(self, data: Dict[str, Any]):
        """Adiciona usuário ao grupo de comentários"""
        try:
            content_type_id = data.get('content_type_id')
            object_id = data.get('object_id')
            
            if not content_type_id or not object_id:
                return
            
            # Verifica se o content_type existe
            content_type = await self.get_content_type(content_type_id)
            if not content_type:
                return
            
            group_name = f'comments_{content_type.app_label}_{content_type.model}_{object_id}'
            
            await self.channel_layer.group_add(
                group_name,
                self.channel_name
            )
            
            self.comment_groups.add(group_name)
            
            # Envia confirmação
            await self.send(text_data=json.dumps({
                'type': 'room_joined',
                'group_name': group_name,
                'user_count': await self.get_group_user_count(group_name)
            }))
            
            logger.info(f'Usuário {self.user.username} entrou no grupo {group_name}')
            
        except Exception as e:
            logger.error(f'Erro ao entrar no grupo de comentários: {e}')
    
    async def leave_comment_room(self, data: Dict[str, Any]):
        """Remove usuário do grupo de comentários"""
        try:
            content_type_id = data.get('content_type_id')
            object_id = data.get('object_id')
            
            if not content_type_id or not object_id:
                return
            
            content_type = await self.get_content_type(content_type_id)
            if not content_type:
                return
            
            group_name = f'comments_{content_type.app_label}_{content_type.model}_{object_id}'
            
            await self.channel_layer.group_discard(
                group_name,
                self.channel_name
            )
            
            self.comment_groups.discard(group_name)
            
            # Envia confirmação
            await self.send(text_data=json.dumps({
                'type': 'room_left',
                'group_name': group_name
            }))
            
            logger.info(f'Usuário {self.user.username} saiu do grupo {group_name}')
            
        except Exception as e:
            logger.error(f'Erro ao sair do grupo de comentários: {e}')
    
    async def handle_typing_indicator(self, data: Dict[str, Any]):
        """Gerencia indicador de digitação"""
        try:
            content_type_id = data.get('content_type_id')
            object_id = data.get('object_id')
            is_typing = data.get('is_typing', False)
            
            if not content_type_id or not object_id:
                return
            
            content_type = await self.get_content_type(content_type_id)
            if not content_type:
                return
            
            group_name = f'comments_{content_type.app_label}_{content_type.model}_{object_id}'
            
            # Envia para outros usuários no grupo
            await self.channel_layer.group_send(
                group_name,
                {
                    'type': 'typing_indicator',
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'is_typing': is_typing
                }
            )
            
        except Exception as e:
            logger.error(f'Erro ao processar indicador de digitação: {e}')
    
    # ==================== MESSAGE HANDLERS ====================
    
    async def send_message(self, event):
        """Envia mensagem para o cliente"""
        await self.send(text_data=json.dumps({
            'type': event['message_type'],
            'data': event['data'],
            'timestamp': event.get('timestamp')
        }))
    
    async def comment_update(self, event):
        """Envia atualização de comentário"""
        await self.send(text_data=json.dumps({
            'type': 'comment_update',
            'action': event['action'],
            'comment': event['comment'],
            'user': event.get('user'),
            'timestamp': event.get('timestamp')
        }))
    
    async def reaction_update(self, event):
        """Envia atualização de reação"""
        await self.send(text_data=json.dumps({
            'type': 'reaction_update',
            'comment_id': event['comment_id'],
            'comment_uuid': event['comment_uuid'],
            'reaction_data': event['reaction_data'],
            'user': event['user'],
            'timestamp': event.get('timestamp')
        }))
    
    async def comment_moderated(self, event):
        """Envia atualização de moderação"""
        await self.send(text_data=json.dumps({
            'type': 'comment_moderated',
            'comment_id': event['comment_id'],
            'comment_uuid': event['comment_uuid'],
            'action': event['action'],
            'new_status': event['new_status'],
            'timestamp': event.get('timestamp')
        }))
    
    async def thread_update(self, event):
        """Envia atualização de thread"""
        await self.send(text_data=json.dumps({
            'type': 'thread_update',
            'action': event['action'],
            'root_comment_id': event['root_comment_id'],
            'affected_comment': event['affected_comment'],
            'thread_stats': event['thread_stats'],
            'timestamp': event.get('timestamp')
        }))
    
    async def typing_indicator(self, event):
        """Envia indicador de digitação"""
        # Não envia para o próprio usuário
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing_indicator',
                'user_id': event['user_id'],
                'username': event['username'],
                'is_typing': event['is_typing']
            }))
    
    async def user_count_update(self, event):
        """Envia atualização de contagem de usuários"""
        await self.send(text_data=json.dumps({
            'type': 'user_count_update',
            'user_count': event['user_count']
        }))
    
    async def notification(self, event):
        """Envia notificação"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event['data']
        }))
    
    async def notification_count_update(self, event):
        """Envia atualização de contagem de notificações"""
        await self.send(text_data=json.dumps({
            'type': 'notification_count_update',
            'unread_count': event['unread_count']
        }))
    
    async def moderation_alert(self, event):
        """Envia alerta de moderação (apenas para moderadores)"""
        if await self.user_is_moderator():
            await self.send(text_data=json.dumps({
                'type': 'moderation_alert',
                'alert_type': event['alert_type'],
                'comment': event['comment'],
                'details': event['details'],
                'priority': event.get('priority', 'normal')
            }))
    
    # ==================== HELPER METHODS ====================
    
    @database_sync_to_async
    def get_content_type(self, content_type_id: int):
        """Obtém ContentType de forma assíncrona"""
        try:
            return ContentType.objects.get(id=content_type_id)
        except ObjectDoesNotExist:
            return None
    
    @database_sync_to_async
    def user_is_moderator(self) -> bool:
        """Verifica se usuário é moderador"""
        return (
            self.user.is_staff or 
            self.user.is_superuser or 
            self.user.groups.filter(name__in=['Moderators', 'Admins']).exists()
        )
    
    async def get_group_user_count(self, group_name: str) -> int:
        """Obtém contagem de usuários no grupo (implementação básica)"""
        # Em implementação real, usaria Redis para contar conexões ativas
        # Por enquanto, retorna valor fixo
        return 1


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    Consumer WebSocket específico para notificações
    
    Gerencia apenas notificações em tempo real para usuários autenticados
    """
    
    async def connect(self):
        """Conecta usuário às notificações"""
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        self.user_group = f'user_{self.user.id}'
        
        await self.channel_layer.group_add(
            self.user_group,
            self.channel_name
        )
        
        await self.accept()
        
        # Envia contagem inicial de notificações não lidas
        unread_count = await self.get_unread_notifications_count()
        await self.send(text_data=json.dumps({
            'type': 'notification_count_update',
            'unread_count': unread_count
        }))
        
        logger.info(f'Usuário {self.user.username} conectado às notificações')
    
    async def disconnect(self, close_code):
        """Desconecta usuário das notificações"""
        await self.channel_layer.group_discard(
            self.user_group,
            self.channel_name
        )
        
        logger.info(f'Usuário {self.user.username} desconectado das notificações')
    
    async def receive(self, text_data):
        """Recebe mensagem do cliente"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'mark_notification_read':
                await self.mark_notification_read(data.get('notification_id'))
            elif message_type == 'mark_all_read':
                await self.mark_all_notifications_read()
            
        except json.JSONDecodeError:
            logger.error('Erro ao decodificar JSON')
        except Exception as e:
            logger.error(f'Erro ao processar mensagem de notificação: {e}')
    
    async def notification(self, event):
        """Envia notificação"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event['data']
        }))
    
    async def notification_count_update(self, event):
        """Envia atualização de contagem"""
        await self.send(text_data=json.dumps({
            'type': 'notification_count_update',
            'unread_count': event['unread_count']
        }))
    
    @database_sync_to_async
    def get_unread_notifications_count(self) -> int:
        """Obtém contagem de notificações não lidas"""
        from .models import CommentNotification
        return CommentNotification.objects.filter(
            recipient=self.user,
            is_read=False
        ).count()
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id: int):
        """Marca notificação como lida"""
        from .models import CommentNotification
        try:
            notification = CommentNotification.objects.get(
                id=notification_id,
                recipient=self.user
            )
            notification.mark_as_read()
        except CommentNotification.DoesNotExist:
            pass
    
    @database_sync_to_async
    def mark_all_notifications_read(self):
        """Marca todas as notificações como lidas"""
        from .models import CommentNotification
        CommentNotification.objects.filter(
            recipient=self.user,
            is_read=False
        ).update(is_read=True)