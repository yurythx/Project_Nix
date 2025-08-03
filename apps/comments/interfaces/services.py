from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.http import HttpRequest

User = get_user_model()


class ICommentService(ABC):
    """
    Interface para serviço de comentários
    
    Define operações de negócio para comentários seguindo
    o princípio de Inversão de Dependência (SOLID)
    """
    
    @abstractmethod
    def get_comment_by_uuid(self, uuid: str) -> Optional['Comment']:
        """Busca comentário por UUID"""
        pass
    
    @abstractmethod
    def get_comments_for_object(self, content_object: Any, user: Optional[User] = None) -> QuerySet:
        """Busca comentários para um objeto"""
        pass
    
    @abstractmethod
    def get_comment_thread(self, root_comment: 'Comment', user: Optional[User] = None) -> List['Comment']:
        """Busca thread completa de comentários"""
        pass
    
    @abstractmethod
    def create_comment(self, content_object: Any, author: User, content: str, 
                      parent: Optional['Comment'] = None, request: Optional[HttpRequest] = None) -> 'Comment':
        """Cria novo comentário"""
        pass
    
    @abstractmethod
    def update_comment(self, comment: 'Comment', content: str, user: User) -> 'Comment':
        """Atualiza comentário"""
        pass
    
    @abstractmethod
    def delete_comment(self, comment: 'Comment', user: User) -> bool:
        """Remove comentário"""
        pass
    
    @abstractmethod
    def toggle_reaction(self, comment: 'Comment', user: User, reaction: str) -> Dict[str, Any]:
        """Adiciona ou remove reação do comentário"""
        pass
    
    @abstractmethod
    def pin_comment(self, comment: 'Comment', user: User) -> 'Comment':
        """Fixa comentário no topo"""
        pass
    
    @abstractmethod
    def unpin_comment(self, comment: 'Comment', user: User) -> 'Comment':
        """Remove fixação do comentário"""
        pass
    
    @abstractmethod
    def get_user_comments(self, user: User, status: Optional[str] = None) -> QuerySet:
        """Busca comentários do usuário"""
        pass
    
    @abstractmethod
    def search_comments(self, query: str, **filters) -> QuerySet:
        """Busca comentários por texto"""
        pass
    
    @abstractmethod
    def get_comment_statistics(self, content_object: Optional[Any] = None) -> Dict[str, int]:
        """Retorna estatísticas de comentários"""
        pass
    
    @abstractmethod
    def can_user_comment(self, user: User, content_object: Any) -> Tuple[bool, str]:
        """Verifica se usuário pode comentar"""
        pass
    
    @abstractmethod
    def can_user_edit_comment(self, user: User, comment: 'Comment') -> bool:
        """Verifica se usuário pode editar comentário"""
        pass
    
    @abstractmethod
    def can_user_delete_comment(self, user: User, comment: 'Comment') -> bool:
        """Verifica se usuário pode deletar comentário"""
        pass


class IModerationService(ABC):
    """
    Interface para serviço de moderação
    
    Define operações de negócio para moderação de comentários
    """
    
    @abstractmethod
    def moderate_comment(self, comment: 'Comment', moderator: User, action: str, reason: str = '') -> 'Comment':
        """Modera comentário"""
        pass
    
    @abstractmethod
    def approve_comment(self, comment: 'Comment', moderator: User, reason: str = '') -> 'Comment':
        """Aprova comentário"""
        pass
    
    @abstractmethod
    def reject_comment(self, comment: 'Comment', moderator: User, reason: str = '') -> 'Comment':
        """Rejeita comentário"""
        pass
    
    @abstractmethod
    def mark_as_spam(self, comment: 'Comment', moderator: User, reason: str = '') -> 'Comment':
        """Marca comentário como spam"""
        pass
    
    @abstractmethod
    def get_moderation_queue(self, moderator: Optional[User] = None) -> QuerySet:
        """Busca fila de moderação"""
        pass
    
    @abstractmethod
    def assign_to_moderator(self, comment: 'Comment', moderator: User) -> 'ModerationQueue':
        """Atribui comentário a moderador"""
        pass
    
    @abstractmethod
    def bulk_moderate(self, comment_ids: List[int], action: str, moderator: User, reason: str = '') -> int:
        """Modera múltiplos comentários"""
        pass
    
    @abstractmethod
    def get_moderation_config(self, content_object: Any) -> 'CommentModeration':
        """Busca configuração de moderação"""
        pass
    
    @abstractmethod
    def update_moderation_config(self, app_label: str, model_name: str, **kwargs) -> 'CommentModeration':
        """Atualiza configuração de moderação"""
        pass
    
    @abstractmethod
    def check_auto_moderation(self, comment: 'Comment', request: Optional[HttpRequest] = None) -> str:
        """Verifica se comentário deve ser moderado automaticamente"""
        pass
    
    @abstractmethod
    def report_comment(self, comment: 'Comment', reporter: User, reason: str = '') -> bool:
        """Reporta comentário"""
        pass
    
    @abstractmethod
    def get_moderation_history(self, comment: 'Comment') -> QuerySet:
        """Busca histórico de moderação"""
        pass
    
    @abstractmethod
    def get_moderator_statistics(self, moderator: User, period_days: int = 30) -> Dict[str, int]:
        """Busca estatísticas do moderador"""
        pass
    
    @abstractmethod
    def is_trusted_user(self, user: User) -> bool:
        """Verifica se usuário é confiável"""
        pass


class INotificationService(ABC):
    """
    Interface para serviço de notificações
    
    Define operações de negócio para notificações de comentários
    """
    
    @abstractmethod
    def create_reply_notification(self, comment: 'Comment') -> Optional['CommentNotification']:
        """Cria notificação para resposta"""
        pass
    
    @abstractmethod
    def create_mention_notifications(self, comment: 'Comment') -> List['CommentNotification']:
        """Cria notificações para menções"""
        pass
    
    @abstractmethod
    def create_like_notification(self, comment: 'Comment', user: User) -> Optional['CommentNotification']:
        """Cria notificação para curtida"""
        pass
    
    @abstractmethod
    def create_moderation_notification(self, comment: 'Comment', action: str, moderator: User, reason: str = '') -> Optional['CommentNotification']:
        """Cria notificação para moderação"""
        pass
    
    @abstractmethod
    def get_user_notifications(self, user: User, is_read: Optional[bool] = None) -> QuerySet:
        """Busca notificações do usuário"""
        pass
    
    @abstractmethod
    def get_unread_count(self, user: User) -> int:
        """Conta notificações não lidas"""
        pass
    
    @abstractmethod
    def mark_as_read(self, notification: 'CommentNotification', user: User) -> bool:
        """Marca notificação como lida"""
        pass
    
    @abstractmethod
    def mark_all_as_read(self, user: User) -> int:
        """Marca todas as notificações como lidas"""
        pass
    
    @abstractmethod
    def send_email_notification(self, notification: 'CommentNotification') -> bool:
        """Envia notificação por email"""
        pass
    
    @abstractmethod
    def send_realtime_notification(self, notification: 'CommentNotification') -> bool:
        """Envia notificação em tempo real"""
        pass
    
    @abstractmethod
    def process_notification_queue(self) -> int:
        """Processa fila de notificações"""
        pass
    
    @abstractmethod
    def get_user_preferences(self, user: User) -> 'NotificationPreference':
        """Busca preferências do usuário"""
        pass
    
    @abstractmethod
    def update_user_preferences(self, user: User, **kwargs) -> 'NotificationPreference':
        """Atualiza preferências do usuário"""
        pass
    
    @abstractmethod
    def send_digest_notifications(self, frequency: str) -> int:
        """Envia resumo de notificações"""
        pass
    
    @abstractmethod
    def cleanup_old_notifications(self, days: int = 30) -> int:
        """Remove notificações antigas"""
        pass


class IWebSocketService(ABC):
    """
    Interface para serviço de WebSocket
    
    Define operações para comunicação em tempo real
    """
    
    @abstractmethod
    def send_to_user(self, user: User, message: Dict[str, Any]) -> bool:
        """Envia mensagem para usuário específico"""
        pass
    
    @abstractmethod
    def send_to_group(self, group_name: str, message: Dict[str, Any]) -> bool:
        """Envia mensagem para grupo"""
        pass
    
    @abstractmethod
    def add_user_to_group(self, user: User, group_name: str) -> bool:
        """Adiciona usuário ao grupo"""
        pass
    
    @abstractmethod
    def remove_user_from_group(self, user: User, group_name: str) -> bool:
        """Remove usuário do grupo"""
        pass
    
    @abstractmethod
    def broadcast_comment_update(self, comment: 'Comment', action: str, user: User) -> bool:
        """Transmite atualização de comentário"""
        pass
    
    @abstractmethod
    def broadcast_notification(self, notification: 'CommentNotification') -> bool:
        """Transmite notificação"""
        pass
    
    @abstractmethod
    def get_online_users(self, group_name: str) -> List[User]:
        """Busca usuários online no grupo"""
        pass
    
    @abstractmethod
    def is_user_online(self, user: User) -> bool:
        """Verifica se usuário está online"""
        pass
    
    @abstractmethod
    def get_group_name_for_object(self, content_object: Any) -> str:
        """Gera nome do grupo para objeto"""
        pass