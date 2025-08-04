from typing import Any, Dict, Optional
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import QuerySet
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.template.loader import render_to_string
import json

from ..models import Comment
from ..services import CommentService, NotificationService, WebSocketService
from ..repositories import (
    DjangoCommentRepository,
    DjangoNotificationRepository,
    DjangoModerationRepository
)
from ..forms import CommentForm, CommentSearchForm
from ..decorators import require_comments_module, CommentsModuleMixin


class CommentServiceMixin:
    """
    Mixin que fornece serviços de comentários para as views
    Segue o padrão SOLID de Injeção de Dependência
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inicializa repositórios
        self.comment_repository = DjangoCommentRepository()
        self.notification_repository = DjangoNotificationRepository()
        self.moderation_repository = DjangoModerationRepository()
        
        # Inicializa serviços
        self.comment_service = CommentService(
            self.comment_repository,
            self.moderation_repository
        )
        self.notification_service = NotificationService(
            self.notification_repository
        )
        self.websocket_service = WebSocketService()


class CommentListView(CommentsModuleMixin, CommentServiceMixin, ListView):
    """
    Lista comentários para um objeto específico
    """
    model = Comment
    template_name = 'comments/comment_list.html'
    context_object_name = 'comments'
    paginate_by = 20
    
    def get_queryset(self) -> QuerySet:
        """Retorna comentários do objeto"""
        content_type_id = self.kwargs.get('content_type_id')
        object_id = self.kwargs.get('object_id')
        
        if not content_type_id or not object_id:
            return Comment.objects.none()
        
        try:
            content_type = ContentType.objects.get(id=content_type_id)
            content_object = content_type.get_object_for_this_type(id=object_id)
            
            return self.comment_service.get_comments_for_object(
                content_object,
                self.request.user if self.request.user.is_authenticated else None
            ).select_related('author', 'parent').prefetch_related('replies')
            
        except (ContentType.DoesNotExist, content_type.model_class().DoesNotExist):
            return Comment.objects.none()
    
    def get(self, request, *args, **kwargs):
        """Handle GET requests, return JSON for AJAX requests"""
        # Check if this is an AJAX request expecting JSON
        if (request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 
            request.headers.get('Accept') == 'application/json'):
            
            try:
                content_type_id = self.kwargs.get('content_type_id')
                object_id = self.kwargs.get('object_id')
                
                if not content_type_id or not object_id:
                    return JsonResponse({
                        'success': False,
                        'error': 'Parâmetros inválidos'
                    }, status=400)
                
                content_type = ContentType.objects.get(id=content_type_id)
                content_object = content_type.get_object_for_this_type(id=object_id)
                
                comments = self.comment_service.get_comments_for_object(
                    content_object,
                    request.user if request.user.is_authenticated else None
                ).select_related('author', 'parent').prefetch_related('replies')
                
                # Render comments as HTML
                comments_html = render_to_string(
                    'comments/partials/comment_list.html',
                    {
                        'comments': comments,
                        'user': request.user,
                        'content_type': content_type,
                        'object_id': object_id,
                    },
                    request=request
                )
                
                return JsonResponse({
                    'success': True,
                    'comments_html': comments_html,
                    'total_comments': comments.count(),
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': 'Erro ao carregar comentários'
                }, status=500)
        
        # Regular HTTP request, return normal template response
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        
        content_type_id = self.kwargs.get('content_type_id')
        object_id = self.kwargs.get('object_id')
        
        if content_type_id and object_id:
            try:
                content_type = ContentType.objects.get(id=content_type_id)
                content_object = content_type.get_object_for_this_type(id=object_id)
                
                context.update({
                    'content_object': content_object,
                    'content_type': content_type,
                    'comment_form': CommentForm(),
                    'can_comment': self.comment_service.can_user_comment(
                        self.request.user, content_object
                    )[0] if self.request.user.is_authenticated else False,
                    'comment_stats': self.comment_service.get_comment_statistics(content_object),
                })
                
            except (ContentType.DoesNotExist, content_type.model_class().DoesNotExist):
                pass
        
        return context


class CommentDetailView(CommentsModuleMixin, CommentServiceMixin, DetailView):
    """
    Exibe detalhes de um comentário específico
    """
    model = Comment
    template_name = 'comments/comment_detail.html'
    context_object_name = 'comment'
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        comment = self.get_object()
        
        context.update({
            'thread': self.comment_service.get_comment_thread(comment),
            'comment_context': self.comment_service.get_comment_context(comment),
            'can_reply': comment.can_have_replies and self.request.user.is_authenticated,
            'can_edit': self.comment_service.can_user_edit_comment(
                self.request.user, comment
            ) if self.request.user.is_authenticated else False,
            'can_delete': self.comment_service.can_user_delete_comment(
                self.request.user, comment
            ) if self.request.user.is_authenticated else False,
        })
        
        return context


class CommentCreateView(CommentsModuleMixin, CommentServiceMixin, LoginRequiredMixin, CreateView):
    """
    Cria novo comentário
    """
    model = Comment
    form_class = CommentForm
    template_name = 'comments/comment_form.html'
    
    def form_valid(self, form):
        """Processa criação do comentário"""
        try:
            # Obtém objeto do comentário
            content_type_id = self.request.POST.get('content_type_id')
            object_id = self.request.POST.get('object_id')
            parent_id = self.request.POST.get('parent_id')
            
            if not content_type_id or not object_id:
                raise ValidationError('Objeto de destino não especificado')
            
            content_type = ContentType.objects.get(id=content_type_id)
            content_object = content_type.get_object_for_this_type(id=object_id)
            
            parent = None
            if parent_id:
                parent = get_object_or_404(Comment, id=parent_id)
            
            # Cria comentário usando o serviço
            comment = self.comment_service.create_comment(
                content_object=content_object,
                author=self.request.user,
                content=form.cleaned_data['content'],
                parent=parent,
                request=self.request
            )
            
            # Resposta AJAX
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'comment': {
                        'id': comment.id,
                        'uuid': str(comment.uuid),
                        'content': comment.content,
                        'author': comment.author.get_full_name() or comment.author.username,
                        'created_at': comment.created_at.isoformat(),
                        'status': comment.status,
                    },
                    'message': 'Comentário criado com sucesso!'
                })
            
            messages.success(self.request, 'Comentário criado com sucesso!')
            return redirect(comment.get_absolute_url())
            
        except (ValidationError, PermissionDenied) as e:
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
            
            form.add_error(None, str(e))
            return self.form_invalid(form)
        
        except Exception as e:
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Erro interno do servidor'
                }, status=500)
            
            form.add_error(None, 'Erro ao criar comentário')
            return self.form_invalid(form)


class CommentUpdateView(CommentsModuleMixin, CommentServiceMixin, LoginRequiredMixin, UpdateView):
    """
    Atualiza comentário existente
    """
    model = Comment
    form_class = CommentForm
    template_name = 'comments/comment_form.html'
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'
    
    def get_object(self, queryset=None):
        """Verifica permissões de edição"""
        comment = super().get_object(queryset)
        
        if not self.comment_service.can_user_edit_comment(self.request.user, comment):
            raise PermissionDenied('Você não pode editar este comentário')
        
        return comment
    
    def form_valid(self, form):
        """Processa atualização do comentário"""
        try:
            comment = self.get_object()
            
            updated_comment = self.comment_service.update_comment(
                comment=comment,
                content=form.cleaned_data['content'],
                user=self.request.user
            )
            
            # Resposta AJAX
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'comment': {
                        'id': updated_comment.id,
                        'content': updated_comment.content,
                        'is_edited': updated_comment.is_edited,
                        'updated_at': updated_comment.updated_at.isoformat(),
                    },
                    'message': 'Comentário atualizado com sucesso!'
                })
            
            messages.success(self.request, 'Comentário atualizado com sucesso!')
            return redirect(updated_comment.get_absolute_url())
            
        except (ValidationError, PermissionDenied) as e:
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
            
            form.add_error(None, str(e))
            return self.form_invalid(form)


class CommentDeleteView(CommentsModuleMixin, CommentServiceMixin, LoginRequiredMixin, DeleteView):
    """
    Remove comentário
    """
    model = Comment
    template_name = 'comments/comment_confirm_delete.html'
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'
    
    def get_object(self, queryset=None):
        """Verifica permissões de deleção"""
        comment = super().get_object(queryset)
        
        if not self.comment_service.can_user_delete_comment(self.request.user, comment):
            raise PermissionDenied('Você não pode deletar este comentário')
        
        return comment
    
    def delete(self, request, *args, **kwargs):
        """Processa deleção do comentário"""
        try:
            comment = self.get_object()
            content_object = comment.content_object
            
            success = self.comment_service.delete_comment(
                comment=comment,
                user=request.user
            )
            
            if success:
                # Resposta AJAX
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'Comentário removido com sucesso!'
                    })
                
                messages.success(request, 'Comentário removido com sucesso!')
                return redirect(content_object.get_absolute_url() if hasattr(content_object, 'get_absolute_url') else '/')
            else:
                raise ValidationError('Erro ao remover comentário')
                
        except (ValidationError, PermissionDenied) as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
            
            messages.error(request, str(e))
            return redirect(self.get_object().get_absolute_url())
    
    def get_success_url(self):
        return reverse_lazy('comments:list')


class CommentReactionView(CommentServiceMixin, LoginRequiredMixin, View):
    """
    Gerencia reações (curtir/descurtir) em comentários
    """
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, uuid):
        """Adiciona ou remove reação"""
        try:
            comment = get_object_or_404(Comment, uuid=uuid)
            
            data = json.loads(request.body) if request.body else {}
            reaction = data.get('reaction', 'like')
            
            if reaction not in ['like', 'dislike']:
                return JsonResponse({
                    'success': False,
                    'error': 'Reação inválida'
                }, status=400)
            
            result = self.comment_service.toggle_reaction(
                comment=comment,
                user=request.user,
                reaction=reaction
            )
            
            return JsonResponse({
                'success': True,
                'data': result
            })
            
        except (ValidationError, PermissionDenied) as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': 'Erro interno do servidor'
            }, status=500)


class CommentSearchView(CommentServiceMixin, ListView):
    """
    Busca comentários
    """
    model = Comment
    template_name = 'comments/comment_search.html'
    context_object_name = 'comments'
    paginate_by = 20
    
    def get_queryset(self) -> QuerySet:
        """Retorna resultados da busca"""
        form = CommentSearchForm(self.request.GET)
        
        if not form.is_valid() or not form.cleaned_data.get('query'):
            return Comment.objects.none()
        
        try:
            return self.comment_service.search_comments(
                query=form.cleaned_data['query'],
                status='approved'
            ).select_related('author', 'content_type')
            
        except ValidationError:
            return Comment.objects.none()
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['search_form'] = CommentSearchForm(self.request.GET)
        context['query'] = self.request.GET.get('query', '')
        return context


class CommentThreadView(CommentServiceMixin, DetailView):
    """
    Exibe thread completa de comentários
    """
    model = Comment
    template_name = 'comments/comment_thread.html'
    context_object_name = 'root_comment'
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        root_comment = self.get_object().get_thread_root()
        
        context.update({
            'thread': self.comment_service.get_comment_thread(root_comment),
            'thread_stats': {
                'total_comments': root_comment.replies_count + 1,
                'max_depth': 3,  # Configurável
            },
            'can_reply': self.request.user.is_authenticated,
        })
        
        return context


# View para carregar mais comentários via AJAX
class LoadMoreCommentsView(CommentServiceMixin, View):
    """
    Carrega mais comentários via AJAX
    """
    
    def get(self, request):
        """Retorna comentários paginados"""
        try:
            content_type_id = request.GET.get('content_type_id')
            object_id = request.GET.get('object_id')
            page = int(request.GET.get('page', 1))
            
            if not content_type_id or not object_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Parâmetros inválidos'
                }, status=400)
            
            content_type = ContentType.objects.get(id=content_type_id)
            content_object = content_type.get_object_for_this_type(id=object_id)
            
            comments = self.comment_service.get_comments_for_object(
                content_object,
                request.user if request.user.is_authenticated else None
            ).select_related('author')
            
            paginator = Paginator(comments, 20)
            page_obj = paginator.get_page(page)
            
            comments_html = render_to_string(
                'comments/partials/comment_list.html',
                {
                    'comments': page_obj.object_list,
                    'user': request.user,
                },
                request=request
            )
            
            return JsonResponse({
                'success': True,
                'html': comments_html,
                'has_next': page_obj.has_next(),
                'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': 'Erro ao carregar comentários'
            }, status=500)