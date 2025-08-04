"""Views unificadas para comentários no app mangas
Exemplo de como usar o service unificado de comentários"""

import logging
from django.views.generic import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views import View

from ..models.capitulo import Capitulo
from ..models.manga import Manga
from apps.comments.services.unified_comment_service import create_comment_service
from apps.comments.exceptions import CommentNotFoundError, CommentValidationError
from apps.comments.decorators import require_comments_module, CommentsModuleMixin

logger = logging.getLogger(__name__)

class MangaCommentCreateView(CommentsModuleMixin, LoginRequiredMixin, View):
    """
    View para criar comentários em mangás usando service unificado
    
    ANTES: Sistema duplicado com ChapterComment
    DEPOIS: Usa Comment genérico via UnifiedCommentService
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.comment_service = create_comment_service()
    
    def post(self, request, manga_slug):
        """Cria comentário no mangá"""
        try:
            # Obtém o mangá
            manga = get_object_or_404(Manga, slug=manga_slug, is_published=True)
            
            # Obtém dados do formulário
            content = request.POST.get('content', '').strip()
            parent_id = request.POST.get('parent_id')
            
            if not content:
                messages.error(request, "Conteúdo do comentário é obrigatório")
                return JsonResponse({'error': 'Conteúdo obrigatório'}, status=400)
            
            # Obtém comentário pai se especificado
            parent = None
            if parent_id:
                try:
                    from apps.comments.models.comment import Comment
                    parent = Comment.objects.get(id=parent_id)
                except Comment.DoesNotExist:
                    messages.error(request, "Comentário pai não encontrado")
                    return JsonResponse({'error': 'Comentário pai inválido'}, status=400)
            
            # Cria comentário usando service unificado
            comment = self.comment_service.create_comment(
                content=content,
                author=request.user,
                content_object=manga,
                parent=parent
            )
            
            messages.success(request, "Comentário criado com sucesso!")
            
            # Retorna dados do comentário para AJAX
            return JsonResponse({
                'success': True,
                'comment': {
                    'id': comment.id,
                    'content': comment.content,
                    'author': comment.author.username,
                    'created_at': comment.created_at.isoformat(),
                    'status': comment.status
                }
            })
            
        except CommentValidationError as e:
            messages.error(request, str(e))
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            logger.error(f"Erro ao criar comentário no mangá {manga_slug}: {e}")
            messages.error(request, "Erro interno do servidor")
            return JsonResponse({'error': 'Erro interno'}, status=500)

class ChapterCommentCreateView(CommentsModuleMixin, LoginRequiredMixin, View):
    """
    View para criar comentários em capítulos usando service unificado
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.comment_service = create_comment_service()
    
    def post(self, request, manga_slug, chapter_slug):
        """Cria comentário no capítulo"""
        try:
            # Obtém o capítulo
            chapter = get_object_or_404(
                Capitulo,
                slug=chapter_slug,
                volume__manga__slug=manga_slug,
                is_published=True
            )
            
            content = request.POST.get('content', '').strip()
            parent_id = request.POST.get('parent_id')
            
            if not content:
                return JsonResponse({'error': 'Conteúdo obrigatório'}, status=400)
            
            # Comentário pai (se for resposta)
            parent = None
            if parent_id:
                try:
                    from apps.comments.models.comment import Comment
                    parent = Comment.objects.get(id=parent_id)
                except Comment.DoesNotExist:
                    return JsonResponse({'error': 'Comentário pai inválido'}, status=400)
            
            # Cria comentário
            comment = self.comment_service.create_comment(
                content=content,
                author=request.user,
                content_object=chapter,
                parent=parent
            )
            
            return JsonResponse({
                'success': True,
                'comment': {
                    'id': comment.id,
                    'content': comment.content,
                    'author': comment.author.username,
                    'created_at': comment.created_at.isoformat(),
                    'status': comment.status
                }
            })
            
        except CommentValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            logger.error(f"Erro ao criar comentário no capítulo {chapter_slug}: {e}")
            return JsonResponse({'error': 'Erro interno'}, status=500)

class CommentUpdateView(CommentsModuleMixin, LoginRequiredMixin, View):
    """
    View unificada para atualizar comentários
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.comment_service = create_comment_service()
    
    def post(self, request, comment_id):
        """Atualiza comentário"""
        try:
            content = request.POST.get('content', '').strip()
            
            if not content:
                return JsonResponse({'error': 'Conteúdo obrigatório'}, status=400)
            
            # Atualiza usando service
            comment = self.comment_service.update_comment(
                comment_id=comment_id,
                content=content,
                user=request.user
            )
            
            return JsonResponse({
                'success': True,
                'comment': {
                    'id': comment.id,
                    'content': comment.content,
                    'is_edited': comment.is_edited,
                    'updated_at': comment.updated_at.isoformat()
                }
            })
            
        except CommentNotFoundError:
            return JsonResponse({'error': 'Comentário não encontrado'}, status=404)
        except CommentValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            logger.error(f"Erro ao atualizar comentário {comment_id}: {e}")
            return JsonResponse({'error': 'Erro interno'}, status=500)

class CommentDeleteView(CommentsModuleMixin, LoginRequiredMixin, View):
    """
    View unificada para deletar comentários
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.comment_service = create_comment_service()
    
    def post(self, request, comment_id):
        """Deleta comentário"""
        try:
            self.comment_service.delete_comment(
                comment_id=comment_id,
                user=request.user
            )
            
            return JsonResponse({'success': True})
            
        except CommentNotFoundError:
            return JsonResponse({'error': 'Comentário não encontrado'}, status=404)
        except CommentValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            logger.error(f"Erro ao deletar comentário {comment_id}: {e}")
            return JsonResponse({'error': 'Erro interno'}, status=500)

class CommentModerationView(CommentsModuleMixin, LoginRequiredMixin, View):
    """
    View para moderação de comentários (apenas staff)
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.comment_service = create_comment_service()
    
    def post(self, request, comment_id):
        """Modera comentário"""
        try:
            if not request.user.is_staff:
                return JsonResponse({'error': 'Sem permissão'}, status=403)
            
            action = request.POST.get('action')  # approve, reject, spam
            
            if action not in ['approve', 'reject', 'spam']:
                return JsonResponse({'error': 'Ação inválida'}, status=400)
            
            comment = self.comment_service.moderate_comment(
                comment_id=comment_id,
                action=action,
                moderator=request.user
            )
            
            return JsonResponse({
                'success': True,
                'comment': {
                    'id': comment.id,
                    'status': comment.status
                }
            })
            
        except CommentNotFoundError:
            return JsonResponse({'error': 'Comentário não encontrado'}, status=404)
        except CommentValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            logger.error(f"Erro ao moderar comentário {comment_id}: {e}")
            return JsonResponse({'error': 'Erro interno'}, status=500)

# Mixin para adicionar comentários a views existentes
class CommentContextMixin:
    """
    Mixin para adicionar contexto de comentários a qualquer view
    
    Uso:
    class MangaDetailView(CommentContextMixin, DetailView):
        # Automaticamente adiciona comentários ao contexto
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.comment_service = create_comment_service()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Adiciona comentários do objeto atual
        if hasattr(self, 'object') and self.object:
            comments = self.comment_service.get_comments_for_object(
                self.object,
                include_pending=self.request.user.is_staff
            )
            
            stats = self.comment_service.get_comment_stats(self.object)
            
            context.update({
                'comments': comments,
                'comment_stats': stats,
                'can_moderate': self.request.user.is_staff
            })
        
        return context