from typing import List, Optional, Dict, Any
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet, Q, Count, Prefetch
from django.db import transaction
from django.utils import timezone

from ..interfaces.repositories import ICommentRepository
from ..models import Comment, CommentLike

User = get_user_model()


class DjangoCommentRepository(ICommentRepository):
    """
    Implementação Django do repositório de comentários
    
    Implementa ICommentRepository seguindo os princípios SOLID:
    - Single Responsibility: Apenas operações de dados de comentários
    - Open/Closed: Extensível via herança
    - Liskov Substitution: Pode substituir ICommentRepository
    - Interface Segregation: Interface específica para comentários
    - Dependency Inversion: Depende da abstração ICommentRepository
    """
    
    def get_by_id(self, comment_id: int) -> Optional[Comment]:
        """Busca comentário por ID"""
        try:
            return Comment.objects.select_related(
                'author', 'parent', 'content_type', 'moderated_by'
            ).get(id=comment_id)
        except Comment.DoesNotExist:
            return None
    
    def get_by_uuid(self, uuid: str) -> Optional[Comment]:
        """Busca comentário por UUID"""
        try:
            return Comment.objects.select_related(
                'author', 'parent', 'content_type', 'moderated_by'
            ).get(uuid=uuid)
        except Comment.DoesNotExist:
            return None
    
    def get_for_object(self, content_object: Any, status: str = 'approved') -> QuerySet:
        """Busca comentários para um objeto específico"""
        content_type = ContentType.objects.get_for_model(content_object)
        
        queryset = Comment.objects.filter(
            content_type=content_type,
            object_id=content_object.pk
        ).select_related(
            'author', 'parent', 'moderated_by'
        ).prefetch_related(
            Prefetch(
                'replies',
                queryset=Comment.objects.filter(status='approved').select_related('author')
            )
        )
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-is_pinned', '-created_at')
    
    def get_replies(self, parent_comment: Comment, status: str = 'approved') -> QuerySet:
        """Busca respostas de um comentário"""
        queryset = Comment.objects.filter(
            parent=parent_comment
        ).select_related(
            'author', 'moderated_by'
        )
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-is_pinned', 'created_at')
    
    def get_by_author(self, author: User, status: Optional[str] = None) -> QuerySet:
        """Busca comentários de um autor"""
        queryset = Comment.objects.filter(
            author=author
        ).select_related(
            'content_type', 'parent', 'moderated_by'
        )
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-created_at')
    
    def get_pending_moderation(self) -> QuerySet:
        """Busca comentários pendentes de moderação"""
        return Comment.objects.filter(
            status='pending'
        ).select_related(
            'author', 'content_type', 'parent'
        ).order_by('-created_at')
    
    def get_recent_comments(self, limit: int = 10) -> QuerySet:
        """Busca comentários recentes"""
        return Comment.objects.filter(
            status='approved'
        ).select_related(
            'author', 'content_type'
        ).order_by('-created_at')[:limit]
    
    @transaction.atomic
    def create(self, **kwargs) -> Comment:
        """Cria novo comentário"""
        comment = Comment.objects.create(**kwargs)
        
        # Atualiza contador do comentário pai se existir
        if comment.parent:
            comment.parent.update_replies_count()
        
        return comment
    
    @transaction.atomic
    def update(self, comment: Comment, **kwargs) -> Comment:
        """Atualiza comentário"""
        # Marca como editado se o conteúdo foi alterado
        if 'content' in kwargs and kwargs['content'] != comment.content:
            kwargs['is_edited'] = True
        
        for field, value in kwargs.items():
            setattr(comment, field, value)
        
        comment.save()
        return comment
    
    @transaction.atomic
    def delete(self, comment: Comment) -> bool:
        """Remove comentário"""
        parent = comment.parent
        comment.delete()
        
        # Atualiza contador do comentário pai se existir
        if parent:
            parent.update_replies_count()
        
        return True
    
    @transaction.atomic
    def bulk_update_status(self, comment_ids: List[int], status: str) -> int:
        """Atualiza status de múltiplos comentários"""
        updated = Comment.objects.filter(
            id__in=comment_ids
        ).update(
            status=status,
            moderated_at=timezone.now()
        )
        
        return updated
    
    def get_statistics(self, content_object: Optional[Any] = None) -> Dict[str, int]:
        """Retorna estatísticas de comentários"""
        queryset = Comment.objects.all()
        
        if content_object:
            content_type = ContentType.objects.get_for_model(content_object)
            queryset = queryset.filter(
                content_type=content_type,
                object_id=content_object.pk
            )
        
        stats = queryset.aggregate(
            total=Count('id'),
            approved=Count('id', filter=Q(status='approved')),
            pending=Count('id', filter=Q(status='pending')),
            rejected=Count('id', filter=Q(status__in=['rejected', 'spam', 'deleted'])),
            with_replies=Count('id', filter=Q(replies_count__gt=0)),
        )
        
        # Adiciona estatísticas de reações
        reaction_stats = CommentLike.objects.filter(
            comment__in=queryset
        ).aggregate(
            total_likes=Count('id', filter=Q(reaction='like')),
            total_dislikes=Count('id', filter=Q(reaction='dislike')),
        )
        
        stats.update(reaction_stats)
        return stats
    
    def search(self, query: str, **filters) -> QuerySet:
        """Busca comentários por texto"""
        queryset = Comment.objects.filter(
            content__icontains=query
        ).select_related(
            'author', 'content_type', 'parent'
        )
        
        # Aplica filtros adicionais
        if 'status' in filters:
            queryset = queryset.filter(status=filters['status'])
        
        if 'author' in filters:
            queryset = queryset.filter(author=filters['author'])
        
        if 'content_type' in filters:
            queryset = queryset.filter(content_type=filters['content_type'])
        
        if 'date_from' in filters:
            queryset = queryset.filter(created_at__gte=filters['date_from'])
        
        if 'date_to' in filters:
            queryset = queryset.filter(created_at__lte=filters['date_to'])
        
        return queryset.order_by('-created_at')
    
    def get_user_reaction(self, comment: Comment, user: User) -> Optional[CommentLike]:
        """Busca reação do usuário ao comentário"""
        try:
            return CommentLike.objects.get(comment=comment, user=user)
        except CommentLike.DoesNotExist:
            return None
    
    @transaction.atomic
    def add_reaction(self, comment: Comment, user: User, reaction: str) -> CommentLike:
        """Adiciona reação ao comentário"""
        # Remove reação anterior se existir
        CommentLike.objects.filter(comment=comment, user=user).delete()
        
        # Cria nova reação
        like = CommentLike.objects.create(
            comment=comment,
            user=user,
            reaction=reaction
        )
        
        return like
    
    @transaction.atomic
    def remove_reaction(self, comment: Comment, user: User) -> bool:
        """Remove reação do comentário"""
        deleted, _ = CommentLike.objects.filter(
            comment=comment,
            user=user
        ).delete()
        
        return deleted > 0
    
    def get_thread(self, root_comment: Comment, max_depth: int = 3) -> List[Comment]:
        """Busca thread completa de comentários"""
        def get_replies_recursive(comment, current_depth=0):
            if current_depth >= max_depth:
                return []
            
            replies = list(self.get_replies(comment, status='approved'))
            result = []
            
            for reply in replies:
                result.append(reply)
                result.extend(get_replies_recursive(reply, current_depth + 1))
            
            return result
        
        thread = [root_comment]
        thread.extend(get_replies_recursive(root_comment))
        
        return thread
    
    def get_comments_with_reactions(self, content_object: Any, user: Optional[User] = None) -> QuerySet:
        """Busca comentários com informações de reações"""
        queryset = self.get_for_object(content_object)
        
        # Adiciona contadores de reações
        queryset = queryset.annotate(
            user_reaction=Count(
                'reactions',
                filter=Q(reactions__user=user) if user else Q(pk=None)
            )
        )
        
        return queryset
    
    def get_top_comments(self, content_object: Any, limit: int = 5) -> QuerySet:
        """Busca comentários mais populares"""
        return self.get_for_object(content_object).annotate(
            popularity_score=(
                Count('reactions', filter=Q(reactions__reaction='like')) * 2 +
                Count('replies', filter=Q(replies__status='approved')) * 3
            )
        ).order_by('-popularity_score', '-created_at')[:limit]
    
    def get_user_comment_count(self, user: User, period_days: Optional[int] = None) -> int:
        """Conta comentários do usuário em um período"""
        queryset = Comment.objects.filter(author=user)
        
        if period_days:
            since = timezone.now() - timezone.timedelta(days=period_days)
            queryset = queryset.filter(created_at__gte=since)
        
        return queryset.count()
    
    def get_comments_by_ip(self, ip_address: str, period_hours: int = 24) -> QuerySet:
        """Busca comentários por IP em um período"""
        since = timezone.now() - timezone.timedelta(hours=period_hours)
        
        return Comment.objects.filter(
            ip_address=ip_address,
            created_at__gte=since
        ).order_by('-created_at')