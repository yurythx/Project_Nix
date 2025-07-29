"""
Views API para o sistema de comentários.
"""

import json
from typing import Dict, Any
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views import View

from ...models.comments import ChapterComment, CommentReaction, CommentReport
from ...models.capitulo import Capitulo
from ...services.comment_service import CommentService
from ...services.moderation_service import ModerationService

comment_service = CommentService()
moderation_service = ModerationService()

class CommentAPIView(View):
    """
    View base para APIs de comentários.
    """
    
    def dispatch(self, request, *args, **kwargs):
        """Adiciona CSRF exemption para APIs."""
        return super().dispatch(request, *args, **kwargs)

@method_decorator(csrf_exempt, name='dispatch')
class ChapterCommentsView(CommentAPIView):
    """
    API para listar comentários de um capítulo.
    """
    
    def get(self, request: HttpRequest, chapter_id: int) -> JsonResponse:
        """Obtém comentários de um capítulo."""
        try:
            capitulo = Capitulo.objects.get(id=chapter_id, is_published=True)
        except Capitulo.DoesNotExist:
            return JsonResponse({'error': 'Capítulo não encontrado'}, status=404)
        
        page = int(request.GET.get('page', 1))
        filter_type = request.GET.get('filter', 'all')
        sort_by = request.GET.get('sort', 'newest')
        
        # Obter comentários
        comments_data = comment_service.get_chapter_comments(
            capitulo=capitulo,
            page=page,
            user=request.user
        )
        
        # Serializar comentários
        comments = []
        for comment in comments_data['page_obj']:
            comment_data = self._serialize_comment(comment)
            comments.append(comment_data)
        
        return JsonResponse({
            'comments': comments,
            'pagination': {
                'current_page': page,
                'total_pages': comments_data['total_pages'],
                'total_comments': comments_data['total_comments'],
                'has_next': comments_data['page_obj'].has_next(),
                'has_previous': comments_data['page_obj'].has_previous(),
            }
        })
    
    def post(self, request: HttpRequest, chapter_id: int) -> JsonResponse:
        """Cria um novo comentário."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Usuário não autenticado'}, status=401)
        
        try:
            capitulo = Capitulo.objects.get(id=chapter_id, is_published=True)
        except Capitulo.DoesNotExist:
            return JsonResponse({'error': 'Capítulo não encontrado'}, status=404)
        
        try:
            data = json.loads(request.body)
            content = data.get('content', '').strip()
            parent_id = data.get('parent_id')
            page_number = data.get('page_number')
            
            if not content:
                return JsonResponse({'error': 'Conteúdo não pode estar vazio'}, status=400)
            
            # Criar comentário
            comment = comment_service.create_comment(
                user=request.user,
                capitulo=capitulo,
                content=content,
                parent_id=parent_id,
                page_number=page_number
            )
            
            # Moderar comentário
            moderation_actions = moderation_service.moderate_comment(comment)
            
            # Verificar se foi deletado automaticamente
            if any(action.action_type == 'auto_delete' for action in moderation_actions):
                return JsonResponse({
                    'error': 'Comentário removido automaticamente por violar as regras da comunidade'
                }, status=400)
            
            return JsonResponse({
                'success': True,
                'comment': self._serialize_comment(comment),
                'moderation_warning': len(moderation_actions) > 0
            })
            
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'error': 'Erro interno do servidor'}, status=500)
    
    def _serialize_comment(self, comment: ChapterComment) -> Dict[str, Any]:
        """Serializa um comentário para JSON."""
        return {
            'id': comment.id,
            'content': comment.content,
            'user': {
                'id': comment.user.id,
                'username': comment.user.username,
                'avatar_url': comment.user.avatar.url if comment.user.avatar else None,
            },
            'page_number': comment.page_number,
            'is_edited': comment.is_edited,
            'edited_at': comment.edited_at.isoformat() if comment.edited_at else None,
            'created_at': comment.created_at.isoformat(),
            'is_reply': comment.is_reply,
            'reply_count': comment.reply_count,
            'user_reactions': getattr(comment, 'user_reactions', {}),
            'reaction_counts': getattr(comment, 'reaction_counts', {}),
            'can_edit': getattr(comment, 'can_edit', False),
            'can_delete': getattr(comment, 'can_delete', False),
            'can_report': getattr(comment, 'can_report', False),
            'replies': [self._serialize_comment(reply) for reply in comment.replies.all()],
        }

@method_decorator(csrf_exempt, name='dispatch')
class CommentDetailView(CommentAPIView):
    """
    API para operações em comentários específicos.
    """
    
    def put(self, request: HttpRequest, comment_id: int) -> JsonResponse:
        """Atualiza um comentário."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Usuário não autenticado'}, status=401)
        
        try:
            comment = ChapterComment.objects.get(id=comment_id)
        except ChapterComment.DoesNotExist:
            return JsonResponse({'error': 'Comentário não encontrado'}, status=404)
        
        try:
            data = json.loads(request.body)
            content = data.get('content', '').strip()
            
            if not content:
                return JsonResponse({'error': 'Conteúdo não pode estar vazio'}, status=400)
            
            # Atualizar comentário
            updated_comment = comment_service.update_comment(
                comment=comment,
                user=request.user,
                content=content
            )
            
            return JsonResponse({
                'success': True,
                'comment': self._serialize_comment(updated_comment)
            })
            
        except (ValueError, PermissionError) as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'error': 'Erro interno do servidor'}, status=500)
    
    def delete(self, request: HttpRequest, comment_id: int) -> JsonResponse:
        """Deleta um comentário."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Usuário não autenticado'}, status=401)
        
        try:
            comment = ChapterComment.objects.get(id=comment_id)
        except ChapterComment.DoesNotExist:
            return JsonResponse({'error': 'Comentário não encontrado'}, status=404)
        
        try:
            success = comment_service.delete_comment(comment, request.user)
            return JsonResponse({'success': success})
        except PermissionError as e:
            return JsonResponse({'error': str(e)}, status=403)
        except Exception as e:
            return JsonResponse({'error': 'Erro interno do servidor'}, status=500)
    
    def _serialize_comment(self, comment: ChapterComment) -> Dict[str, Any]:
        """Serializa um comentário para JSON."""
        return {
            'id': comment.id,
            'content': comment.content,
            'user': {
                'id': comment.user.id,
                'username': comment.user.username,
                'avatar_url': comment.user.avatar.url if comment.user.avatar else None,
            },
            'page_number': comment.page_number,
            'is_edited': comment.is_edited,
            'edited_at': comment.edited_at.isoformat() if comment.edited_at else None,
            'created_at': comment.created_at.isoformat(),
        }

@method_decorator(csrf_exempt, name='dispatch')
class CommentReactionView(CommentAPIView):
    """
    API para reações em comentários.
    """
    
    def post(self, request: HttpRequest, comment_id: int) -> JsonResponse:
        """Adiciona uma reação a um comentário."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Usuário não autenticado'}, status=401)
        
        try:
            comment = ChapterComment.objects.get(id=comment_id)
        except ChapterComment.DoesNotExist:
            return JsonResponse({'error': 'Comentário não encontrado'}, status=404)
        
        try:
            data = json.loads(request.body)
            reaction_type = data.get('reaction_type')
            
            if not reaction_type:
                return JsonResponse({'error': 'Tipo de reação é obrigatório'}, status=400)
            
            # Adicionar reação
            reaction = comment_service.add_reaction(
                user=request.user,
                comment=comment,
                reaction_type=reaction_type
            )
            
            # Obter contadores atualizados
            reaction_counts = comment_service._get_reaction_counts(comment)
            
            return JsonResponse({
                'success': True,
                'reaction': {
                    'type': reaction.reaction_type,
                    'display': reaction.get_reaction_type_display()
                },
                'reaction_counts': reaction_counts
            })
            
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'error': 'Erro interno do servidor'}, status=500)
    
    def delete(self, request: HttpRequest, comment_id: int) -> JsonResponse:
        """Remove a reação do usuário de um comentário."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Usuário não autenticado'}, status=401)
        
        try:
            comment = ChapterComment.objects.get(id=comment_id)
        except ChapterComment.DoesNotExist:
            return JsonResponse({'error': 'Comentário não encontrado'}, status=404)
        
        try:
            success = comment_service.remove_reaction(request.user, comment)
            
            if success:
                # Obter contadores atualizados
                reaction_counts = comment_service._get_reaction_counts(comment)
                return JsonResponse({
                    'success': True,
                    'reaction_counts': reaction_counts
                })
            else:
                return JsonResponse({'error': 'Reação não encontrada'}, status=404)
                
        except Exception as e:
            return JsonResponse({'error': 'Erro interno do servidor'}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class CommentReportView(CommentAPIView):
    """
    API para reportar comentários.
    """
    
    def post(self, request: HttpRequest, comment_id: int) -> JsonResponse:
        """Reporta um comentário."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Usuário não autenticado'}, status=401)
        
        try:
            comment = ChapterComment.objects.get(id=comment_id)
        except ChapterComment.DoesNotExist:
            return JsonResponse({'error': 'Comentário não encontrado'}, status=404)
        
        try:
            data = json.loads(request.body)
            reason = data.get('reason')
            description = data.get('description', '').strip()
            
            if not reason:
                return JsonResponse({'error': 'Motivo é obrigatório'}, status=400)
            
            # Reportar comentário
            report = comment_service.report_comment(
                user=request.user,
                comment=comment,
                reason=reason,
                description=description
            )
            
            return JsonResponse({
                'success': True,
                'report_id': report.id
            })
            
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'error': 'Erro interno do servidor'}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class UserCommentsView(CommentAPIView):
    """
    API para comentários de um usuário específico.
    """
    
    def get(self, request: HttpRequest, user_id: int = None) -> JsonResponse:
        """Obtém comentários de um usuário."""
        if user_id is None:
            user_id = request.user.id
        
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Usuário não autenticado'}, status=401)
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Usuário não encontrado'}, status=404)
        
        page = int(request.GET.get('page', 1))
        
        # Obter comentários do usuário
        comments_data = comment_service.get_user_comments(user, page)
        
        # Serializar comentários
        comments = []
        for comment in comments_data['page_obj']:
            comment_data = {
                'id': comment.id,
                'content': comment.content,
                'created_at': comment.created_at.isoformat(),
                'capitulo': {
                    'id': comment.capitulo.id,
                    'number': comment.capitulo.number,
                    'manga': {
                        'id': comment.capitulo.manga.id,
                        'title': comment.capitulo.manga.title,
                    }
                }
            }
            comments.append(comment_data)
        
        return JsonResponse({
            'comments': comments,
            'pagination': {
                'current_page': page,
                'total_pages': comments_data['total_pages'],
                'total_comments': comments_data['total_comments'],
                'has_next': comments_data['page_obj'].has_next(),
                'has_previous': comments_data['page_obj'].has_previous(),
            }
        })

@method_decorator(csrf_exempt, name='dispatch')
class CommentStatsView(CommentAPIView):
    """
    API para estatísticas de comentários.
    """
    
    def get(self, request: HttpRequest, chapter_id: int) -> JsonResponse:
        """Obtém estatísticas de comentários de um capítulo."""
        try:
            capitulo = Capitulo.objects.get(id=chapter_id)
        except Capitulo.DoesNotExist:
            return JsonResponse({'error': 'Capítulo não encontrado'}, status=404)
        
        stats = comment_service.get_comment_stats(capitulo)
        
        return JsonResponse({
            'stats': stats
        }) 