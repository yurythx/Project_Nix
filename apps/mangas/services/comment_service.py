"""
Serviço para gerenciar comentários em capítulos de mangá.
"""

import logging
from typing import List, Dict, Any, Optional
from django.db.models import Q, Count, Prefetch
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.utils import timezone
from django.core.cache import cache

from ..models.comments import ChapterComment, CommentReaction, CommentReport
from ..models.capitulo import Capitulo

logger = logging.getLogger(__name__)
User = get_user_model()

class CommentService:
    """
    Serviço para gerenciar comentários em capítulos.
    """
    
    def __init__(self):
        self.comments_per_page = 20
        self.cache_timeout = 300  # 5 minutos
    
    def get_chapter_comments(self, capitulo: Capitulo, page: int = 1, 
                           user: Optional[User] = None) -> Dict[str, Any]:
        """
        Obtém comentários de um capítulo com paginação.
        """
        cache_key = f'chapter_comments_{capitulo.id}_page_{page}'
        cached_data = cache.get(cache_key)
        
        if cached_data is None:
            # Buscar comentários principais (não são respostas)
            comments = ChapterComment.objects.filter(
                capitulo=capitulo,
                parent=None,
                is_deleted=False
            ).select_related('user').prefetch_related(
                Prefetch(
                    'replies',
                    queryset=ChapterComment.objects.filter(
                        is_deleted=False
                    ).select_related('user').order_by('created_at')
                ),
                'reactions'
            ).order_by('-created_at')
            
            # Paginação
            paginator = Paginator(comments, self.comments_per_page)
            page_obj = paginator.get_page(page)
            
            # Adicionar informações extras para cada comentário
            for comment in page_obj:
                comment.user_reactions = self._get_user_reactions(comment, user)
                comment.reaction_counts = self._get_reaction_counts(comment)
                comment.can_edit = self._can_edit_comment(comment, user)
                comment.can_delete = self._can_delete_comment(comment, user)
                comment.can_report = self._can_report_comment(comment, user)
            
            cached_data = {
                'page_obj': page_obj,
                'total_comments': paginator.count,
                'total_pages': paginator.num_pages,
            }
            cache.set(cache_key, cached_data, self.cache_timeout)
        
        return cached_data
    
    def create_comment(self, user: User, capitulo: Capitulo, content: str, 
                      parent_id: Optional[int] = None, page_number: Optional[int] = None) -> ChapterComment:
        """
        Cria um novo comentário.
        """
        # Validações
        if not content.strip():
            raise ValueError("O conteúdo do comentário não pode estar vazio.")
        
        if len(content) > 2000:
            raise ValueError("O comentário não pode ter mais de 2000 caracteres.")
        
        # Verificar se é uma resposta válida
        parent = None
        if parent_id:
            try:
                parent = ChapterComment.objects.get(
                    id=parent_id,
                    capitulo=capitulo,
                    is_deleted=False
                )
            except ChapterComment.DoesNotExist:
                raise ValueError("Comentário pai não encontrado.")
        
        # Verificar se a página existe (se especificada)
        if page_number and page_number > capitulo.paginas.count():
            raise ValueError("Número de página inválido.")
        
        # Criar comentário
        comment = ChapterComment.objects.create(
            user=user,
            capitulo=capitulo,
            parent=parent,
            content=content.strip(),
            page_number=page_number
        )
        
        # Limpar cache
        self._clear_chapter_comments_cache(capitulo)
        
        logger.info(f"Comentário criado: {comment.id} por {user.username}")
        return comment
    
    def update_comment(self, comment: ChapterComment, user: User, content: str) -> ChapterComment:
        """
        Atualiza um comentário existente.
        """
        if not self._can_edit_comment(comment, user):
            raise PermissionError("Você não tem permissão para editar este comentário.")
        
        if not content.strip():
            raise ValueError("O conteúdo do comentário não pode estar vazio.")
        
        if len(content) > 2000:
            raise ValueError("O comentário não pode ter mais de 2000 caracteres.")
        
        # Verificar se passou muito tempo desde a criação
        time_diff = timezone.now() - comment.created_at
        if time_diff.total_seconds() > 3600:  # 1 hora
            raise ValueError("Comentários só podem ser editados até 1 hora após a criação.")
        
        comment.content = content.strip()
        comment.mark_as_edited()
        comment.save()
        
        # Limpar cache
        self._clear_chapter_comments_cache(comment.capitulo)
        
        logger.info(f"Comentário editado: {comment.id} por {user.username}")
        return comment
    
    def delete_comment(self, comment: ChapterComment, user: User) -> bool:
        """
        Deleta um comentário (soft delete).
        """
        if not self._can_delete_comment(comment, user):
            raise PermissionError("Você não tem permissão para deletar este comentário.")
        
        comment.soft_delete()
        
        # Limpar cache
        self._clear_chapter_comments_cache(comment.capitulo)
        
        logger.info(f"Comentário deletado: {comment.id} por {user.username}")
        return True
    
    def add_reaction(self, user: User, comment: ChapterComment, reaction_type: str) -> CommentReaction:
        """
        Adiciona uma reação a um comentário.
        """
        if reaction_type not in dict(CommentReaction.REACTION_TYPES):
            raise ValueError("Tipo de reação inválido.")
        
        # Verificar se já existe uma reação do usuário
        reaction, created = CommentReaction.objects.get_or_create(
            user=user,
            comment=comment,
            defaults={'reaction_type': reaction_type}
        )
        
        if not created:
            # Atualizar reação existente
            reaction.reaction_type = reaction_type
            reaction.save()
        
        # Limpar cache
        self._clear_chapter_comments_cache(comment.capitulo)
        
        logger.info(f"Reação adicionada: {reaction_type} por {user.username}")
        return reaction
    
    def remove_reaction(self, user: User, comment: ChapterComment) -> bool:
        """
        Remove a reação do usuário de um comentário.
        """
        try:
            reaction = CommentReaction.objects.get(user=user, comment=comment)
            reaction.delete()
            
            # Limpar cache
            self._clear_chapter_comments_cache(comment.capitulo)
            
            logger.info(f"Reação removida por {user.username}")
            return True
        except CommentReaction.DoesNotExist:
            return False
    
    def report_comment(self, user: User, comment: ChapterComment, reason: str, 
                      description: str = "") -> CommentReport:
        """
        Reporta um comentário.
        """
        if reason not in dict(CommentReport.REPORT_REASONS):
            raise ValueError("Motivo de denúncia inválido.")
        
        if comment.user == user:
            raise ValueError("Você não pode denunciar seu próprio comentário.")
        
        # Verificar se já denunciou
        if CommentReport.objects.filter(reporter=user, comment=comment).exists():
            raise ValueError("Você já denunciou este comentário.")
        
        report = CommentReport.objects.create(
            reporter=user,
            comment=comment,
            reason=reason,
            description=description.strip()
        )
        
        logger.info(f"Comentário reportado: {comment.id} por {user.username}")
        return report
    
    def get_user_comments(self, user: User, page: int = 1) -> Dict[str, Any]:
        """
        Obtém comentários de um usuário específico.
        """
        comments = ChapterComment.objects.filter(
            user=user,
            is_deleted=False
        ).select_related('capitulo__manga').order_by('-created_at')
        
        paginator = Paginator(comments, self.comments_per_page)
        page_obj = paginator.get_page(page)
        
        return {
            'page_obj': page_obj,
            'total_comments': paginator.count,
            'total_pages': paginator.num_pages,
        }
    
    def get_page_comments(self, capitulo: Capitulo, page_number: int) -> List[ChapterComment]:
        """
        Obtém comentários de uma página específica.
        """
        return ChapterComment.objects.filter(
            capitulo=capitulo,
            page_number=page_number,
            is_deleted=False
        ).select_related('user').order_by('created_at')
    
    def get_comment_stats(self, capitulo: Capitulo) -> Dict[str, int]:
        """
        Obtém estatísticas de comentários de um capítulo.
        """
        cache_key = f'comment_stats_{capitulo.id}'
        stats = cache.get(cache_key)
        
        if stats is None:
            stats = {
                'total_comments': ChapterComment.objects.filter(
                    capitulo=capitulo,
                    is_deleted=False
                ).count(),
                'total_replies': ChapterComment.objects.filter(
                    capitulo=capitulo,
                    parent__isnull=False,
                    is_deleted=False
                ).count(),
                'total_reactions': CommentReaction.objects.filter(
                    comment__capitulo=capitulo
                ).count(),
            }
            cache.set(cache_key, stats, self.cache_timeout)
        
        return stats
    
    def _get_user_reactions(self, comment: ChapterComment, user: Optional[User]) -> Dict[str, Any]:
        """Obtém reações do usuário para um comentário."""
        if not user or not user.is_authenticated:
            return {}
        
        try:
            reaction = CommentReaction.objects.get(user=user, comment=comment)
            return {
                'type': reaction.reaction_type,
                'display': reaction.get_reaction_type_display()
            }
        except CommentReaction.DoesNotExist:
            return {}
    
    def _get_reaction_counts(self, comment: ChapterComment) -> Dict[str, int]:
        """Obtém contagem de reações por tipo."""
        counts = {}
        for reaction_type, _ in CommentReaction.REACTION_TYPES:
            counts[reaction_type] = comment.reactions.filter(
                reaction_type=reaction_type
            ).count()
        return counts
    
    def _can_edit_comment(self, comment: ChapterComment, user: Optional[User]) -> bool:
        """Verifica se o usuário pode editar o comentário."""
        if not user or not user.is_authenticated:
            return False
        
        # Autor do comentário pode editar
        if comment.user == user:
            return True
        
        # Staff pode editar
        if user.is_staff:
            return True
        
        return False
    
    def _can_delete_comment(self, comment: ChapterComment, user: Optional[User]) -> bool:
        """Verifica se o usuário pode deletar o comentário."""
        if not user or not user.is_authenticated:
            return False
        
        # Autor do comentário pode deletar
        if comment.user == user:
            return True
        
        # Staff pode deletar
        if user.is_staff:
            return True
        
        return False
    
    def _can_report_comment(self, comment: ChapterComment, user: Optional[User]) -> bool:
        """Verifica se o usuário pode reportar o comentário."""
        if not user or not user.is_authenticated:
            return False
        
        # Não pode reportar próprio comentário
        if comment.user == user:
            return False
        
        # Verificar se já reportou
        if CommentReport.objects.filter(reporter=user, comment=comment).exists():
            return False
        
        return True
    
    def _clear_chapter_comments_cache(self, capitulo: Capitulo):
        """Limpa cache de comentários do capítulo."""
        # Limpar cache de todas as páginas
        for page in range(1, 11):  # Assumindo máximo 10 páginas
            cache_key = f'chapter_comments_{capitulo.id}_page_{page}'
            cache.delete(cache_key)
        
        # Limpar cache de estatísticas
        cache.delete(f'comment_stats_{capitulo.id}') 