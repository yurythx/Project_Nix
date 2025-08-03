from typing import List, Optional, Dict, Any, Tuple
from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.http import HttpRequest
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
from django.db import transaction
import re

from ..interfaces.services import ICommentService
from ..interfaces.repositories import ICommentRepository, IModerationRepository
from ..models import Comment

User = get_user_model()


class CommentService(ICommentService):
    """
    Serviço principal para gerenciamento de comentários
    
    Implementa ICommentService seguindo os princípios SOLID:
    - Single Responsibility: Apenas lógica de negócio de comentários
    - Open/Closed: Extensível via herança
    - Liskov Substitution: Pode substituir ICommentService
    - Interface Segregation: Interface específica para comentários
    - Dependency Inversion: Depende de abstrações (interfaces)
    """
    
    def __init__(self, comment_repository: ICommentRepository, moderation_repository: IModerationRepository):
        self.comment_repository = comment_repository
        self.moderation_repository = moderation_repository
    
    def get_comment_by_uuid(self, uuid: str) -> Optional[Comment]:
        """Busca comentário por UUID"""
        return self.comment_repository.get_by_uuid(uuid)
    
    def get_comments_for_object(self, content_object: Any, user: Optional[User] = None) -> QuerySet:
        """Busca comentários para um objeto"""
        # Busca apenas comentários raiz (sem pai) aprovados
        comments = self.comment_repository.get_for_object(content_object, status='approved')
        
        # Filtra apenas comentários raiz
        comments = comments.filter(parent__isnull=True)
        
        return comments
    
    def get_comment_thread(self, root_comment: Comment, user: Optional[User] = None) -> List[Comment]:
        """Busca thread completa de comentários"""
        return self.comment_repository.get_thread(root_comment, max_depth=3)
    
    @transaction.atomic
    def create_comment(self, content_object: Any, author: User, content: str, 
                      parent: Optional[Comment] = None, request: Optional[HttpRequest] = None) -> Comment:
        """Cria novo comentário"""
        # Validações
        can_comment, reason = self.can_user_comment(author, content_object)
        if not can_comment:
            raise PermissionDenied(reason)
        
        # Valida conteúdo
        content = content.strip()
        if len(content) < 3:
            raise ValidationError('Comentário deve ter pelo menos 3 caracteres')
        
        if len(content) > 2000:
            raise ValidationError('Comentário não pode ter mais de 2000 caracteres')
        
        # Valida comentário pai
        if parent:
            if not parent.can_have_replies:
                raise ValidationError('Este comentário não pode receber respostas')
            
            if parent.content_object != content_object:
                raise ValidationError('Comentário pai deve ser do mesmo objeto')
        
        # Extrai metadados da requisição
        ip_address = None
        user_agent = ''
        
        if request:
            ip_address = self._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        
        # Determina status inicial baseado na moderação
        content_type = ContentType.objects.get_for_model(content_object)
        moderation_config = self.moderation_repository.get_moderation_config(
            content_type.app_label,
            content_type.model
        )
        
        status = 'pending'
        if moderation_config:
            if moderation_config.should_auto_approve(author, content, ip_address):
                status = 'approved'
        elif author.is_staff:
            status = 'approved'
        
        # Cria comentário
        comment = self.comment_repository.create(
            content=content,
            author=author,
            content_object=content_object,
            parent=parent,
            status=status,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Adiciona à fila de moderação se necessário
        if status == 'pending':
            self.moderation_repository.add_to_queue(comment)
        
        return comment
    
    @transaction.atomic
    def update_comment(self, comment: Comment, content: str, user: User) -> Comment:
        """Atualiza comentário"""
        if not self.can_user_edit_comment(user, comment):
            raise PermissionDenied('Você não pode editar este comentário')
        
        # Valida conteúdo
        content = content.strip()
        if len(content) < 3:
            raise ValidationError('Comentário deve ter pelo menos 3 caracteres')
        
        if len(content) > 2000:
            raise ValidationError('Comentário não pode ter mais de 2000 caracteres')
        
        # Atualiza comentário
        return self.comment_repository.update(
            comment,
            content=content,
            is_edited=True
        )
    
    @transaction.atomic
    def delete_comment(self, comment: Comment, user: User) -> bool:
        """Remove comentário"""
        if not self.can_user_delete_comment(user, comment):
            raise PermissionDenied('Você não pode deletar este comentário')
        
        # Se tem respostas, marca como deletado ao invés de remover
        if comment.replies.exists():
            self.comment_repository.update(
                comment,
                content='[Comentário removido]',
                status='deleted'
            )
            return True
        else:
            return self.comment_repository.delete(comment)
    
    @transaction.atomic
    def toggle_reaction(self, comment: Comment, user: User, reaction: str) -> Dict[str, Any]:
        """Adiciona ou remove reação do comentário"""
        if not user.is_authenticated:
            raise PermissionDenied('Você precisa estar logado para reagir')
        
        if reaction not in ['like', 'dislike']:
            raise ValidationError('Reação inválida')
        
        # Verifica reação atual
        current_reaction = self.comment_repository.get_user_reaction(comment, user)
        
        if current_reaction:
            if current_reaction.reaction == reaction:
                # Remove reação
                self.comment_repository.remove_reaction(comment, user)
                action = 'removed'
            else:
                # Altera reação
                self.comment_repository.add_reaction(comment, user, reaction)
                action = 'changed'
        else:
            # Adiciona nova reação
            self.comment_repository.add_reaction(comment, user, reaction)
            action = 'added'
        
        # Atualiza contadores
        comment.update_reaction_counts()
        comment.refresh_from_db()
        
        return {
            'action': action,
            'reaction': reaction,
            'likes_count': comment.likes_count,
            'dislikes_count': comment.dislikes_count,
        }
    
    @transaction.atomic
    def pin_comment(self, comment: Comment, user: User) -> Comment:
        """Fixa comentário no topo"""
        if not user.is_staff:
            raise PermissionDenied('Apenas moderadores podem fixar comentários')
        
        return self.comment_repository.update(comment, is_pinned=True)
    
    @transaction.atomic
    def unpin_comment(self, comment: Comment, user: User) -> Comment:
        """Remove fixação do comentário"""
        if not user.is_staff:
            raise PermissionDenied('Apenas moderadores podem desfixar comentários')
        
        return self.comment_repository.update(comment, is_pinned=False)
    
    def get_user_comments(self, user: User, status: Optional[str] = None) -> QuerySet:
        """Busca comentários do usuário"""
        return self.comment_repository.get_by_author(user, status)
    
    def search_comments(self, query: str, **filters) -> QuerySet:
        """Busca comentários por texto"""
        if len(query.strip()) < 3:
            raise ValidationError('Busca deve ter pelo menos 3 caracteres')
        
        return self.comment_repository.search(query, **filters)
    
    def get_comment_statistics(self, content_object: Optional[Any] = None) -> Dict[str, int]:
        """Retorna estatísticas de comentários"""
        return self.comment_repository.get_statistics(content_object)
    
    def can_user_comment(self, user: User, content_object: Any) -> Tuple[bool, str]:
        """Verifica se usuário pode comentar"""
        if not user.is_authenticated:
            return False, 'Você precisa estar logado para comentar'
        
        # Verifica se email está verificado
        if hasattr(user, 'is_verified') and not user.is_verified:
            return False, 'Você precisa verificar seu email para comentar'
        
        # Verifica rate limiting
        content_type = ContentType.objects.get_for_model(content_object)
        moderation_config = self.moderation_repository.get_moderation_config(
            content_type.app_label,
            content_type.model
        )
        
        if moderation_config:
            if not moderation_config.check_rate_limit(user):
                return False, 'Você atingiu o limite de comentários. Tente novamente mais tarde'
        
        return True, ''
    
    def can_user_edit_comment(self, user: User, comment: Comment) -> bool:
        """Verifica se usuário pode editar comentário"""
        return comment.can_be_edited_by(user)
    
    def can_user_delete_comment(self, user: User, comment: Comment) -> bool:
        """Verifica se usuário pode deletar comentário"""
        return comment.can_be_deleted_by(user)
    
    def extract_mentions(self, content: str) -> List[str]:
        """Extrai menções (@username) do conteúdo"""
        # Regex para encontrar @username
        mention_pattern = r'@([a-zA-Z0-9_]+)'
        mentions = re.findall(mention_pattern, content)
        
        # Remove duplicatas mantendo ordem
        seen = set()
        unique_mentions = []
        for mention in mentions:
            if mention not in seen:
                seen.add(mention)
                unique_mentions.append(mention)
        
        return unique_mentions
    
    def get_mentioned_users(self, content: str) -> List[User]:
        """Busca usuários mencionados no conteúdo"""
        mentions = self.extract_mentions(content)
        
        if not mentions:
            return []
        
        return list(User.objects.filter(
            username__in=mentions,
            is_active=True
        ))
    
    def get_popular_comments(self, content_object: Any, limit: int = 5) -> QuerySet:
        """Busca comentários mais populares"""
        return self.comment_repository.get_top_comments(content_object, limit)
    
    def get_recent_activity(self, user: User, days: int = 7) -> Dict[str, Any]:
        """Busca atividade recente do usuário"""
        since = timezone.now() - timezone.timedelta(days=days)
        
        comments = self.comment_repository.get_by_author(user).filter(
            created_at__gte=since
        )
        
        return {
            'comments_count': comments.count(),
            'approved_count': comments.filter(status='approved').count(),
            'pending_count': comments.filter(status='pending').count(),
            'total_likes': sum(c.likes_count for c in comments),
            'total_replies': sum(c.replies_count for c in comments),
        }
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Extrai IP do cliente da requisição"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def moderate_user_content(self, user: User, action: str, moderator: User) -> int:
        """Modera todo o conteúdo de um usuário"""
        if not moderator.is_staff:
            raise PermissionDenied('Apenas moderadores podem realizar esta ação')
        
        if action not in ['approve', 'reject', 'spam']:
            raise ValidationError('Ação inválida')
        
        status_map = {
            'approve': 'approved',
            'reject': 'rejected',
            'spam': 'spam'
        }
        
        comment_ids = list(
            self.comment_repository.get_by_author(user, status='pending').values_list('id', flat=True)
        )
        
        if comment_ids:
            return self.comment_repository.bulk_update_status(comment_ids, status_map[action])
        
        return 0
    
    def get_comment_context(self, comment: Comment) -> Dict[str, Any]:
        """Retorna contexto completo do comentário"""
        return {
            'comment': comment,
            'thread': self.get_comment_thread(comment.get_thread_root()),
            'content_object': comment.content_object,
            'author_stats': self.get_recent_activity(comment.author),
            'can_reply': comment.can_have_replies,
        }