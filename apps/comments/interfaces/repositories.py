from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet

User = get_user_model()


class ICommentRepository(ABC):
    """
    Interface para repositório de comentários
    
    Define operações de acesso a dados para comentários seguindo
    o princípio de Inversão de Dependência (SOLID)
    """
    
    @abstractmethod
    def get_by_id(self, comment_id: int) -> Optional['Comment']:
        """Busca comentário por ID"""
        pass
    
    @abstractmethod
    def get_by_uuid(self, uuid: str) -> Optional['Comment']:
        """Busca comentário por UUID"""
        pass
    
    @abstractmethod
    def get_for_object(self, content_object: Any, status: str = 'approved') -> QuerySet:
        """Busca comentários para um objeto específico"""
        pass
    
    @abstractmethod
    def get_replies(self, parent_comment: 'Comment', status: str = 'approved') -> QuerySet:
        """Busca respostas de um comentário"""
        pass
    
    @abstractmethod
    def get_by_author(self, author: User, status: Optional[str] = None) -> QuerySet:
        """Busca comentários de um autor"""
        pass
    
    @abstractmethod
    def get_pending_moderation(self) -> QuerySet:
        """Busca comentários pendentes de moderação"""
        pass
    
    @abstractmethod
    def get_recent_comments(self, limit: int = 10) -> QuerySet:
        """Busca comentários recentes"""
        pass
    
    @abstractmethod
    def create(self, **kwargs) -> 'Comment':
        """Cria novo comentário"""
        pass
    
    @abstractmethod
    def update(self, comment: 'Comment', **kwargs) -> 'Comment':
        """Atualiza comentário"""
        pass
    
    @abstractmethod
    def delete(self, comment: 'Comment') -> bool:
        """Remove comentário"""
        pass
    
    @abstractmethod
    def bulk_update_status(self, comment_ids: List[int], status: str) -> int:
        """Atualiza status de múltiplos comentários"""
        pass
    
    @abstractmethod
    def get_statistics(self, content_object: Optional[Any] = None) -> Dict[str, int]:
        """Retorna estatísticas de comentários"""
        pass
    
    @abstractmethod
    def search(self, query: str, **filters) -> QuerySet:
        """Busca comentários por texto"""
        pass
    
    @abstractmethod
    def get_user_reaction(self, comment: 'Comment', user: User) -> Optional['CommentLike']:
        """Busca reação do usuário ao comentário"""
        pass
    
    @abstractmethod
    def add_reaction(self, comment: 'Comment', user: User, reaction: str) -> 'CommentLike':
        """Adiciona reação ao comentário"""
        pass
    
    @abstractmethod
    def remove_reaction(self, comment: 'Comment', user: User) -> bool:
        """Remove reação do comentário"""
        pass
    
    @abstractmethod
    def get_thread(self, root_comment: 'Comment', max_depth: int = 3) -> List['Comment']:
        """Busca thread completa de comentários"""
        pass


class IModerationRepository(ABC):
    """
    Interface para repositório de moderação
    
    Define operações de acesso a dados para moderação de comentários
    """
    
    @abstractmethod
    def get_moderation_config(self, app_label: str, model_name: str) -> Optional['CommentModeration']:
        """Busca configuração de moderação"""
        pass
    
    @abstractmethod
    def create_moderation_config(self, **kwargs) -> 'CommentModeration':
        """Cria configuração de moderação"""
        pass
    
    @abstractmethod
    def update_moderation_config(self, config: 'CommentModeration', **kwargs) -> 'CommentModeration':
        """Atualiza configuração de moderação"""
        pass
    
    @abstractmethod
    def get_moderation_queue(self, assigned_to: Optional[User] = None) -> QuerySet:
        """Busca fila de moderação"""
        pass
    
    @abstractmethod
    def add_to_queue(self, comment: 'Comment', priority: str = 'normal') -> 'ModerationQueue':
        """Adiciona comentário à fila de moderação"""
        pass
    
    @abstractmethod
    def remove_from_queue(self, comment: 'Comment') -> bool:
        """Remove comentário da fila de moderação"""
        pass
    
    @abstractmethod
    def assign_to_moderator(self, queue_item: 'ModerationQueue', moderator: User) -> 'ModerationQueue':
        """Atribui item da fila a moderador"""
        pass
    
    @abstractmethod
    def create_moderation_action(self, **kwargs) -> 'ModerationAction':
        """Cria registro de ação de moderação"""
        pass
    
    @abstractmethod
    def get_moderation_history(self, comment: 'Comment') -> QuerySet:
        """Busca histórico de moderação"""
        pass
    
    @abstractmethod
    def get_moderator_stats(self, moderator: User, period_days: int = 30) -> Dict[str, int]:
        """Busca estatísticas do moderador"""
        pass
    
    @abstractmethod
    def check_rate_limit(self, user: User, config: 'CommentModeration') -> bool:
        """Verifica limite de comentários do usuário"""
        pass
    
    @abstractmethod
    def is_spam_suspected(self, content: str, user: User, ip_address: str) -> bool:
        """Verifica se comentário é suspeito de spam"""
        pass


class INotificationRepository(ABC):
    """
    Interface para repositório de notificações
    
    Define operações de acesso a dados para notificações de comentários
    """
    
    @abstractmethod
    def get_by_id(self, notification_id: int) -> Optional['CommentNotification']:
        """Busca notificação por ID"""
        pass
    
    @abstractmethod
    def get_by_uuid(self, uuid: str) -> Optional['CommentNotification']:
        """Busca notificação por UUID"""
        pass
    
    @abstractmethod
    def get_for_user(self, user: User, is_read: Optional[bool] = None) -> QuerySet:
        """Busca notificações do usuário"""
        pass
    
    @abstractmethod
    def get_unread_count(self, user: User) -> int:
        """Conta notificações não lidas"""
        pass
    
    @abstractmethod
    def create(self, **kwargs) -> 'CommentNotification':
        """Cria nova notificação"""
        pass
    
    @abstractmethod
    def mark_as_read(self, notification: 'CommentNotification') -> 'CommentNotification':
        """Marca notificação como lida"""
        pass
    
    @abstractmethod
    def mark_all_as_read(self, user: User) -> int:
        """Marca todas as notificações como lidas"""
        pass
    
    @abstractmethod
    def delete_old_notifications(self, days: int = 30) -> int:
        """Remove notificações antigas"""
        pass
    
    @abstractmethod
    def get_pending_email_notifications(self) -> QuerySet:
        """Busca notificações pendentes de envio por email"""
        pass
    
    @abstractmethod
    def mark_as_sent(self, notification: 'CommentNotification') -> 'CommentNotification':
        """Marca notificação como enviada"""
        pass
    
    @abstractmethod
    def get_user_preferences(self, user: User) -> 'NotificationPreference':
        """Busca preferências de notificação do usuário"""
        pass
    
    @abstractmethod
    def update_user_preferences(self, user: User, **kwargs) -> 'NotificationPreference':
        """Atualiza preferências de notificação"""
        pass
    
    @abstractmethod
    def get_digest_notifications(self, user: User, frequency: str) -> QuerySet:
        """Busca notificações para resumo"""
        pass
    
    @abstractmethod
    def bulk_create(self, notifications: List[Dict[str, Any]]) -> List['CommentNotification']:
        """Cria múltiplas notificações"""
        pass