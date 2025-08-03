"""Service unificado para comentários
Solução para o problema de duplicação entre apps comments e mangas"""

import logging
from typing import Dict, Any, Optional, List, Union
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.db.models import QuerySet, Q
from django.core.exceptions import ValidationError

from ..models.comment import Comment
from ..interfaces.services import ICommentService
from ..exceptions import CommentNotFoundError, CommentValidationError

logger = logging.getLogger(__name__)

class UnifiedCommentService(ICommentService):
    """
    Service unificado para comentários que pode ser usado por qualquer app
    
    Resolve o problema de duplicação entre:
    - apps.comments.models.Comment (sistema genérico)
    - apps.mangas.models.comments.ChapterComment (específico)
    
    Permite comentários em qualquer modelo usando ContentType
    """
    
    def create_comment(self, content: str, author: User, content_object: Any, parent: Optional[Comment] = None) -> Comment:
        """
        Cria comentário para qualquer tipo de objeto
        
        Args:
            content: Conteúdo do comentário
            author: Usuário autor
            content_object: Objeto sendo comentado (Manga, Chapter, Article, etc.)
            parent: Comentário pai (para respostas)
        """
        try:
            # Validações
            if not content or not content.strip():
                raise CommentValidationError("Conteúdo do comentário é obrigatório")
            
            if len(content) > 1000:  # Limite configurável
                raise CommentValidationError("Comentário muito longo (máximo 1000 caracteres)")
            
            # Obtém ContentType do objeto
            content_type = ContentType.objects.get_for_model(content_object)
            
            # Cria comentário
            comment = Comment.objects.create(
                content=content.strip(),
                author=author,
                content_type=content_type,
                object_id=content_object.pk,
                parent=parent,
                status='approved' if author.is_staff else 'pending'  # Auto-aprova staff
            )
            
            logger.info(f"Comentário criado: {comment.id} por {author.username}")
            return comment
            
        except Exception as e:
            logger.error(f"Erro ao criar comentário: {e}")
            raise CommentValidationError(f"Erro ao criar comentário: {str(e)}")
    
    def get_comments_for_object(self, content_object: Any, include_pending: bool = False) -> QuerySet[Comment]:
        """
        Obtém comentários para um objeto específico
        
        Args:
            content_object: Objeto cujos comentários queremos
            include_pending: Se deve incluir comentários pendentes
        """
        try:
            content_type = ContentType.objects.get_for_model(content_object)
            
            queryset = Comment.objects.filter(
                content_type=content_type,
                object_id=content_object.pk,
                parent__isnull=True  # Apenas comentários principais
            ).select_related('author').prefetch_related('replies')
            
            if not include_pending:
                queryset = queryset.filter(status='approved')
            
            return queryset.order_by('-created_at')
            
        except Exception as e:
            logger.error(f"Erro ao obter comentários: {e}")
            return Comment.objects.none()
    
    def get_comment_replies(self, comment: Comment) -> QuerySet[Comment]:
        """Obtém respostas de um comentário"""
        return comment.replies.filter(status='approved').select_related('author').order_by('created_at')
    
    def update_comment(self, comment_id: int, content: str, user: User) -> Comment:
        """Atualiza comentário (apenas autor ou staff)"""
        try:
            comment = Comment.objects.get(id=comment_id)
            
            # Verifica permissões
            if comment.author != user and not user.is_staff:
                raise CommentValidationError("Sem permissão para editar este comentário")
            
            # Validações
            if not content or not content.strip():
                raise CommentValidationError("Conteúdo não pode estar vazio")
            
            # Atualiza
            comment.content = content.strip()
            comment.is_edited = True
            comment.save(update_fields=['content', 'is_edited', 'updated_at'])
            
            logger.info(f"Comentário {comment_id} atualizado por {user.username}")
            return comment
            
        except Comment.DoesNotExist:
            raise CommentNotFoundError(f"Comentário {comment_id} não encontrado")
        except Exception as e:
            logger.error(f"Erro ao atualizar comentário {comment_id}: {e}")
            raise CommentValidationError(f"Erro ao atualizar comentário: {str(e)}")
    
    def delete_comment(self, comment_id: int, user: User) -> None:
        """Marca comentário como deletado"""
        try:
            comment = Comment.objects.get(id=comment_id)
            
            # Verifica permissões
            if comment.author != user and not user.is_staff:
                raise CommentValidationError("Sem permissão para deletar este comentário")
            
            # Marca como deletado ao invés de excluir
            comment.status = 'deleted'
            comment.save(update_fields=['status', 'updated_at'])
            
            logger.info(f"Comentário {comment_id} deletado por {user.username}")
            
        except Comment.DoesNotExist:
            raise CommentNotFoundError(f"Comentário {comment_id} não encontrado")
        except Exception as e:
            logger.error(f"Erro ao deletar comentário {comment_id}: {e}")
            raise CommentValidationError(f"Erro ao deletar comentário: {str(e)}")
    
    def moderate_comment(self, comment_id: int, action: str, moderator: User) -> Comment:
        """
        Modera comentário (aprovar, rejeitar, marcar como spam)
        
        Args:
            comment_id: ID do comentário
            action: 'approve', 'reject', 'spam'
            moderator: Usuário moderador
        """
        try:
            if not moderator.is_staff:
                raise CommentValidationError("Apenas staff pode moderar comentários")
            
            comment = Comment.objects.get(id=comment_id)
            
            valid_actions = ['approve', 'reject', 'spam']
            if action not in valid_actions:
                raise CommentValidationError(f"Ação inválida. Use: {', '.join(valid_actions)}")
            
            # Mapeia ações para status
            status_map = {
                'approve': 'approved',
                'reject': 'rejected',
                'spam': 'spam'
            }
            
            comment.status = status_map[action]
            comment.save(update_fields=['status', 'updated_at'])
            
            logger.info(f"Comentário {comment_id} {action} por {moderator.username}")
            return comment
            
        except Comment.DoesNotExist:
            raise CommentNotFoundError(f"Comentário {comment_id} não encontrado")
        except Exception as e:
            logger.error(f"Erro ao moderar comentário {comment_id}: {e}")
            raise CommentValidationError(f"Erro na moderação: {str(e)}")
    
    def get_user_comments(self, user: User, include_pending: bool = False) -> QuerySet[Comment]:
        """Obtém comentários de um usuário"""
        queryset = Comment.objects.filter(author=user).select_related('content_type')
        
        if not include_pending:
            queryset = queryset.filter(status='approved')
        
        return queryset.order_by('-created_at')
    
    def get_comment_stats(self, content_object: Any) -> Dict[str, int]:
        """Obtém estatísticas de comentários para um objeto"""
        try:
            content_type = ContentType.objects.get_for_model(content_object)
            
            comments = Comment.objects.filter(
                content_type=content_type,
                object_id=content_object.pk
            )
            
            return {
                'total': comments.count(),
                'approved': comments.filter(status='approved').count(),
                'pending': comments.filter(status='pending').count(),
                'rejected': comments.filter(status='rejected').count(),
                'spam': comments.filter(status='spam').count(),
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {'total': 0, 'approved': 0, 'pending': 0, 'rejected': 0, 'spam': 0}
    
    def search_comments(self, query: str, content_type: Optional[str] = None) -> QuerySet[Comment]:
        """Busca comentários por conteúdo"""
        queryset = Comment.objects.filter(
            Q(content__icontains=query),
            status='approved'
        ).select_related('author', 'content_type')
        
        if content_type:
            try:
                ct = ContentType.objects.get(model=content_type)
                queryset = queryset.filter(content_type=ct)
            except ContentType.DoesNotExist:
                pass
        
        return queryset.order_by('-created_at')

# Factory para criar instância do service
def create_comment_service() -> UnifiedCommentService:
    """Factory para criar service de comentários"""
    return UnifiedCommentService()