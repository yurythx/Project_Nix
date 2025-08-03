from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.generic import View
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
import json

from ..models import Comment, CommentLike
from ..forms import CommentForm, CommentReplyForm, CommentReportForm
from ..interfaces import ICommentService, IModerationService, INotificationService, IWebSocketService
from ..services import CommentService, ModerationService, NotificationService, WebSocketService
from ..repositories import (
    DjangoCommentRepository, DjangoModerationRepository, DjangoNotificationRepository
)


class CommentAPIServiceMixin:
    """
    Mixin para injeção de dependência dos serviços para API
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._comment_service = None
        self._moderation_service = None
        self._notification_service = None
        self._websocket_service = None
    
    @property
    def comment_service(self) -> ICommentService:
        if self._comment_service is None:
            self._comment_service = CommentService(
                DjangoCommentRepository()
            )
        return self._comment_service
    
    @property
    def moderation_service(self) -> IModerationService:
        if self._moderation_service is None:
            self._moderation_service = ModerationService(
                DjangoModerationRepository()
            )
        return self._moderation_service
    
    @property
    def notification_service(self) -> INotificationService:
        if self._notification_service is None:
            self._notification_service = NotificationService(
                DjangoNotificationRepository()
            )
        return self._notification_service
    
    @property
    def websocket_service(self) -> IWebSocketService:
        if self._websocket_service is None:
            self._websocket_service = WebSocketService()
        return self._websocket_service


@method_decorator(csrf_exempt, name='dispatch')
class CommentAPIView(LoginRequiredMixin, CommentAPIServiceMixin, View):
    """
    API para operações CRUD de comentários
    """
    
    def get(self, request, *args, **kwargs):
        """Lista comentários"""
        try:
            # Parâmetros de filtro
            content_type_id = request.GET.get('content_type')
            object_id = request.GET.get('object_id')
            parent_id = request.GET.get('parent')
            page = int(request.GET.get('page', 1))
            per_page = min(int(request.GET.get('per_page', 10)), 50)
            
            if not content_type_id or not object_id:
                return JsonResponse({
                    'error': 'content_type e object_id são obrigatórios'
                }, status=400)
            
            # Obtém o objeto de conteúdo
            content_type = get_object_or_404(ContentType, id=content_type_id)
            content_object = get_object_or_404(content_type.model_class(), id=object_id)
            
            # Busca comentários
            comments = self.comment_service.get_comments_for_object(
                content_object,
                parent_uuid=parent_id
            )
            
            # Paginação
            paginator = Paginator(comments, per_page)
            page_obj = paginator.get_page(page)
            
            # Serializa comentários
            comments_data = []
            for comment in page_obj:
                comment_data = {
                    'id': str(comment.uuid),
                    'content': comment.content,
                    'author': {
                        'id': comment.author.id,
                        'username': comment.author.username,
                        'avatar': getattr(comment.author, 'avatar', None),
                    },
                    'created_at': comment.created_at.isoformat(),
                    'updated_at': comment.updated_at.isoformat(),
                    'likes_count': comment.likes_count,
                    'dislikes_count': comment.dislikes_count,
                    'replies_count': comment.replies_count,
                    'is_pinned': comment.is_pinned,
                    'moderation_status': comment.moderation_status,
                    'depth': comment.depth,
                    'parent_id': str(comment.parent.uuid) if comment.parent else None,
                    'can_edit': comment.author == request.user,
                    'can_delete': comment.author == request.user or request.user.has_perm('comments.delete_comment'),
                }
                
                # Verifica se o usuário curtiu/descurtiu
                if request.user.is_authenticated:
                    user_reaction = CommentLike.objects.filter(
                        comment=comment,
                        user=request.user
                    ).first()
                    
                    comment_data['user_reaction'] = {
                        'liked': user_reaction.is_like if user_reaction else False,
                        'disliked': not user_reaction.is_like if user_reaction else False,
                    }
                
                comments_data.append(comment_data)
            
            return JsonResponse({
                'comments': comments_data,
                'pagination': {
                    'page': page_obj.number,
                    'per_page': per_page,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous(),
                }
            })
        
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)
    
    def post(self, request, *args, **kwargs):
        """Cria novo comentário"""
        try:
            data = json.loads(request.body)
            
            # Validação básica
            content = data.get('content', '').strip()
            content_type_id = data.get('content_type')
            object_id = data.get('object_id')
            parent_id = data.get('parent')
            
            if not content:
                return JsonResponse({
                    'error': 'Conteúdo é obrigatório'
                }, status=400)
            
            if not content_type_id or not object_id:
                return JsonResponse({
                    'error': 'content_type e object_id são obrigatórios'
                }, status=400)
            
            # Obtém o objeto de conteúdo
            content_type = get_object_or_404(ContentType, id=content_type_id)
            content_object = get_object_or_404(content_type.model_class(), id=object_id)
            
            # Cria comentário
            comment = self.comment_service.create_comment(
                user_id=request.user.id,
                content_object=content_object,
                content=content,
                parent_uuid=parent_id,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Notificação em tempo real
            self.websocket_service.send_comment_update(
                str(content_object.pk),
                {
                    'type': 'comment_created',
                    'comment': {
                        'id': str(comment.uuid),
                        'content': comment.content,
                        'author': request.user.username,
                        'created_at': comment.created_at.isoformat(),
                    }
                }
            )
            
            return JsonResponse({
                'success': True,
                'comment': {
                    'id': str(comment.uuid),
                    'content': comment.content,
                    'author': {
                        'id': request.user.id,
                        'username': request.user.username,
                    },
                    'created_at': comment.created_at.isoformat(),
                    'likes_count': 0,
                    'dislikes_count': 0,
                    'replies_count': 0,
                    'is_pinned': False,
                    'moderation_status': comment.moderation_status,
                    'depth': comment.depth,
                    'parent_id': str(comment.parent.uuid) if comment.parent else None,
                }
            })
        
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'JSON inválido'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)
    
    def _get_client_ip(self, request):
        """Obtém IP do cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


@method_decorator(csrf_exempt, name='dispatch')
class CommentDetailAPIView(LoginRequiredMixin, CommentAPIServiceMixin, View):
    """
    API para operações em comentário específico
    """
    
    def get(self, request, comment_id, *args, **kwargs):
        """Obtém detalhes do comentário"""
        try:
            comment = self.comment_service.get_comment_by_uuid(comment_id)
            
            if not comment:
                return JsonResponse({
                    'error': 'Comentário não encontrado'
                }, status=404)
            
            # Verifica permissões
            if comment.moderation_status == 'deleted' and comment.author != request.user:
                return JsonResponse({
                    'error': 'Comentário não encontrado'
                }, status=404)
            
            comment_data = {
                'id': str(comment.uuid),
                'content': comment.content,
                'author': {
                    'id': comment.author.id,
                    'username': comment.author.username,
                },
                'created_at': comment.created_at.isoformat(),
                'updated_at': comment.updated_at.isoformat(),
                'likes_count': comment.likes_count,
                'dislikes_count': comment.dislikes_count,
                'replies_count': comment.replies_count,
                'is_pinned': comment.is_pinned,
                'moderation_status': comment.moderation_status,
                'depth': comment.depth,
                'parent_id': str(comment.parent.uuid) if comment.parent else None,
            }
            
            return JsonResponse(comment_data)
        
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)
    
    def put(self, request, comment_id, *args, **kwargs):
        """Atualiza comentário"""
        try:
            data = json.loads(request.body)
            content = data.get('content', '').strip()
            
            if not content:
                return JsonResponse({
                    'error': 'Conteúdo é obrigatório'
                }, status=400)
            
            comment = self.comment_service.update_comment(
                comment_uuid=comment_id,
                user_id=request.user.id,
                content=content
            )
            
            if not comment:
                return JsonResponse({
                    'error': 'Comentário não encontrado ou sem permissão'
                }, status=404)
            
            # Notificação em tempo real
            self.websocket_service.send_comment_update(
                str(comment.object_id),
                {
                    'type': 'comment_updated',
                    'comment': {
                        'id': str(comment.uuid),
                        'content': comment.content,
                        'updated_at': comment.updated_at.isoformat(),
                    }
                }
            )
            
            return JsonResponse({
                'success': True,
                'comment': {
                    'id': str(comment.uuid),
                    'content': comment.content,
                    'updated_at': comment.updated_at.isoformat(),
                }
            })
        
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'JSON inválido'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)
    
    def delete(self, request, comment_id, *args, **kwargs):
        """Remove comentário"""
        try:
            success = self.comment_service.delete_comment(
                comment_uuid=comment_id,
                user_id=request.user.id
            )
            
            if not success:
                return JsonResponse({
                    'error': 'Comentário não encontrado ou sem permissão'
                }, status=404)
            
            # Notificação em tempo real
            self.websocket_service.send_comment_update(
                comment_id,
                {
                    'type': 'comment_deleted',
                    'comment_id': comment_id,
                }
            )
            
            return JsonResponse({
                'success': True
            })
        
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class CommentReactionAPIView(LoginRequiredMixin, CommentAPIServiceMixin, View):
    """
    API para reações em comentários (curtir/descurtir)
    """
    
    def post(self, request, comment_id, *args, **kwargs):
        """Alterna reação do comentário"""
        try:
            data = json.loads(request.body)
            is_like = data.get('is_like', True)
            
            result = self.comment_service.toggle_reaction(
                comment_uuid=comment_id,
                user_id=request.user.id,
                is_like=is_like
            )
            
            if not result:
                return JsonResponse({
                    'error': 'Comentário não encontrado'
                }, status=404)
            
            # Notificação em tempo real
            self.websocket_service.send_reaction_update(
                comment_id,
                {
                    'likes_count': result['likes_count'],
                    'dislikes_count': result['dislikes_count'],
                    'user_reaction': result['user_reaction'],
                }
            )
            
            return JsonResponse({
                'success': True,
                'likes_count': result['likes_count'],
                'dislikes_count': result['dislikes_count'],
                'user_reaction': result['user_reaction'],
            })
        
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'JSON inválido'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class CommentReportAPIView(LoginRequiredMixin, CommentAPIServiceMixin, View):
    """
    API para reportar comentários
    """
    
    def post(self, request, comment_id, *args, **kwargs):
        """Reporta comentário"""
        try:
            data = json.loads(request.body)
            reason = data.get('reason', 'inappropriate')
            details = data.get('details', '')
            
            success = self.moderation_service.report_comment(
                comment_uuid=comment_id,
                reporter_id=request.user.id,
                reason=reason,
                details=details
            )
            
            if not success:
                return JsonResponse({
                    'error': 'Comentário não encontrado'
                }, status=404)
            
            return JsonResponse({
                'success': True,
                'message': 'Comentário reportado com sucesso'
            })
        
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'JSON inválido'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class CommentPinAPIView(LoginRequiredMixin, CommentAPIServiceMixin, View):
    """
    API para fixar/desfixar comentários
    """
    
    def post(self, request, comment_id, *args, **kwargs):
        """Fixa/desfixa comentário"""
        try:
            # Verifica permissão
            if not request.user.has_perm('comments.pin_comment'):
                return JsonResponse({
                    'error': 'Sem permissão para fixar comentários'
                }, status=403)
            
            result = self.comment_service.toggle_pin(
                comment_uuid=comment_id,
                user_id=request.user.id
            )
            
            if not result:
                return JsonResponse({
                    'error': 'Comentário não encontrado'
                }, status=404)
            
            return JsonResponse({
                'success': True,
                'is_pinned': result['is_pinned']
            })
        
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)


class CommentStatsAPIView(LoginRequiredMixin, CommentAPIServiceMixin, View):
    """
    API para estatísticas de comentários
    """
    
    def get(self, request, *args, **kwargs):
        """Retorna estatísticas de comentários"""
        try:
            content_type_id = request.GET.get('content_type')
            object_id = request.GET.get('object_id')
            
            if content_type_id and object_id:
                # Estatísticas para objeto específico
                content_type = get_object_or_404(ContentType, id=content_type_id)
                content_object = get_object_or_404(content_type.model_class(), id=object_id)
                
                stats = self.comment_service.get_comment_stats(content_object)
            else:
                # Estatísticas gerais do usuário
                stats = self.comment_service.get_user_comment_stats(request.user.id)
            
            return JsonResponse(stats)
        
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)


class CommentSearchAPIView(LoginRequiredMixin, CommentAPIServiceMixin, View):
    """
    API para busca de comentários
    """
    
    def get(self, request, *args, **kwargs):
        """Busca comentários"""
        try:
            query = request.GET.get('q', '').strip()
            page = int(request.GET.get('page', 1))
            per_page = min(int(request.GET.get('per_page', 10)), 50)
            
            if not query or len(query) < 3:
                return JsonResponse({
                    'error': 'Termo de busca deve ter pelo menos 3 caracteres'
                }, status=400)
            
            # Busca comentários
            comments = self.comment_service.search_comments(
                query=query,
                user_id=request.user.id
            )
            
            # Paginação
            paginator = Paginator(comments, per_page)
            page_obj = paginator.get_page(page)
            
            # Serializa resultados
            results = []
            for comment in page_obj:
                results.append({
                    'id': str(comment.uuid),
                    'content': comment.content[:200] + '...' if len(comment.content) > 200 else comment.content,
                    'author': comment.author.username,
                    'created_at': comment.created_at.isoformat(),
                    'content_type': str(comment.content_type),
                    'object_id': comment.object_id,
                })
            
            return JsonResponse({
                'results': results,
                'pagination': {
                    'page': page_obj.number,
                    'per_page': per_page,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                }
            })
        
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)


class CommentThreadAPIView(LoginRequiredMixin, CommentAPIServiceMixin, View):
    """
    API para threads de comentários
    """
    
    def get(self, request, comment_id, *args, **kwargs):
        """Retorna thread completa do comentário"""
        try:
            thread = self.comment_service.get_comment_thread(comment_id)
            
            if not thread:
                return JsonResponse({
                    'error': 'Comentário não encontrado'
                }, status=404)
            
            # Serializa thread
            thread_data = []
            for comment in thread:
                thread_data.append({
                    'id': str(comment.uuid),
                    'content': comment.content,
                    'author': comment.author.username,
                    'created_at': comment.created_at.isoformat(),
                    'depth': comment.depth,
                    'parent_id': str(comment.parent.uuid) if comment.parent else None,
                    'likes_count': comment.likes_count,
                    'dislikes_count': comment.dislikes_count,
                    'replies_count': comment.replies_count,
                })
            
            return JsonResponse({
                'thread': thread_data
            })
        
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)


class NotificationAPIView(LoginRequiredMixin, CommentAPIServiceMixin, View):
    """
    API para notificações
    """
    
    def get(self, request, *args, **kwargs):
        """Lista notificações do usuário"""
        try:
            unread_only = request.GET.get('unread_only', 'false').lower() == 'true'
            page = int(request.GET.get('page', 1))
            per_page = min(int(request.GET.get('per_page', 20)), 50)
            
            notifications = self.notification_service.get_user_notifications(
                user_id=request.user.id,
                unread_only=unread_only
            )
            
            # Paginação
            paginator = Paginator(notifications, per_page)
            page_obj = paginator.get_page(page)
            
            # Serializa notificações
            notifications_data = []
            for notification in page_obj:
                notifications_data.append({
                    'id': str(notification.uuid),
                    'type': notification.notification_type,
                    'message': notification.message,
                    'is_read': notification.is_read,
                    'created_at': notification.created_at.isoformat(),
                    'sender': notification.sender.username if notification.sender else None,
                    'comment_id': str(notification.comment.uuid) if notification.comment else None,
                })
            
            return JsonResponse({
                'notifications': notifications_data,
                'unread_count': self.notification_service.get_unread_count(request.user.id),
                'pagination': {
                    'page': page_obj.number,
                    'per_page': per_page,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                }
            })
        
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class NotificationMarkReadAPIView(LoginRequiredMixin, CommentAPIServiceMixin, View):
    """
    API para marcar notificações como lidas
    """
    
    def post(self, request, notification_id=None, *args, **kwargs):
        """Marca notificação(ões) como lida(s)"""
        try:
            if notification_id:
                # Marca notificação específica
                success = self.notification_service.mark_as_read(
                    request.user.id,
                    notification_id
                )
                
                if not success:
                    return JsonResponse({
                        'error': 'Notificação não encontrada'
                    }, status=404)
            else:
                # Marca todas como lidas
                self.notification_service.mark_all_as_read(request.user.id)
            
            # Atualiza contador em tempo real
            unread_count = self.notification_service.get_unread_count(request.user.id)
            self.websocket_service.send_notification_count_update(
                request.user.id,
                unread_count
            )
            
            return JsonResponse({
                'success': True,
                'unread_count': unread_count
            })
        
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)