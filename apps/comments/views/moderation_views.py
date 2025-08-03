from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, DetailView, FormView, TemplateView
)
from django.http import JsonResponse, HttpResponseForbidden
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta

from ..models import Comment, ModerationQueue, ModerationAction, CommentModeration
from ..forms import (
    ModerationActionForm, BulkModerationForm, CommentModerationConfigForm,
    CommentFilterForm
)
from ..interfaces import IModerationService, INotificationService, IWebSocketService
from ..services import ModerationService, NotificationService, WebSocketService
from ..repositories import (
    DjangoModerationRepository, DjangoNotificationRepository
)


class ModerationServiceMixin:
    """
    Mixin para injeção de dependência dos serviços de moderação
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._moderation_service = None
        self._notification_service = None
        self._websocket_service = None
    
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


class ModerationQueueView(LoginRequiredMixin, PermissionRequiredMixin, 
                         ModerationServiceMixin, ListView):
    """
    View para exibir a fila de moderação
    """
    model = ModerationQueue
    template_name = 'comments/moderation/queue.html'
    context_object_name = 'queue_items'
    paginate_by = 20
    permission_required = 'comments.moderate_comment'
    
    def get_queryset(self):
        """Retorna itens da fila de moderação"""
        queryset = ModerationQueue.objects.select_related(
            'comment__author',
            'comment__content_type',
            'assigned_to'
        ).filter(
            is_resolved=False
        ).order_by('-priority', '-created_at')
        
        # Filtros
        filter_form = CommentFilterForm(self.request.GET)
        if filter_form.is_valid():
            if filter_form.cleaned_data.get('author'):
                queryset = queryset.filter(
                    comment__author=filter_form.cleaned_data['author']
                )
            
            if filter_form.cleaned_data.get('date_from'):
                queryset = queryset.filter(
                    created_at__date__gte=filter_form.cleaned_data['date_from']
                )
            
            if filter_form.cleaned_data.get('date_to'):
                queryset = queryset.filter(
                    created_at__date__lte=filter_form.cleaned_data['date_to']
                )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = CommentFilterForm(self.request.GET)
        context['stats'] = self.moderation_service.get_moderation_stats()
        context['pending_count'] = ModerationQueue.objects.filter(
            is_resolved=False
        ).count()
        return context


class ModerationDetailView(LoginRequiredMixin, PermissionRequiredMixin,
                          ModerationServiceMixin, DetailView):
    """
    View para exibir detalhes de um item da fila de moderação
    """
    model = ModerationQueue
    template_name = 'comments/moderation/detail.html'
    context_object_name = 'queue_item'
    permission_required = 'comments.moderate_comment'
    
    def get_object(self):
        obj = super().get_object()
        # Atribui automaticamente ao moderador atual se não estiver atribuído
        if not obj.assigned_to:
            obj.assigned_to = self.request.user
            obj.save()
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action_form'] = ModerationActionForm()
        context['comment_history'] = ModerationAction.objects.filter(
            comment=self.object.comment
        ).select_related('moderator').order_by('-created_at')
        return context


class ModerationActionView(LoginRequiredMixin, PermissionRequiredMixin,
                          ModerationServiceMixin, FormView):
    """
    View para executar ações de moderação
    """
    form_class = ModerationActionForm
    permission_required = 'comments.moderate_comment'
    
    def form_valid(self, form):
        queue_id = self.kwargs.get('pk')
        queue_item = get_object_or_404(ModerationQueue, pk=queue_id)
        
        action = form.cleaned_data['action']
        reason = form.cleaned_data.get('reason', '')
        notify_user = form.cleaned_data.get('notify_user', True)
        
        try:
            if action == 'approve':
                self.moderation_service.approve_comment(
                    queue_item.comment.uuid,
                    self.request.user.id,
                    reason
                )
                messages.success(self.request, 'Comentário aprovado com sucesso')
            
            elif action == 'reject':
                self.moderation_service.reject_comment(
                    queue_item.comment.uuid,
                    self.request.user.id,
                    reason
                )
                messages.success(self.request, 'Comentário rejeitado com sucesso')
            
            elif action == 'spam':
                self.moderation_service.mark_as_spam(
                    queue_item.comment.uuid,
                    self.request.user.id,
                    reason
                )
                messages.success(self.request, 'Comentário marcado como spam')
            
            # Notifica o usuário se solicitado
            if notify_user:
                self.notification_service.create_moderation_notification(
                    queue_item.comment.author.id,
                    queue_item.comment.uuid,
                    action,
                    reason
                )
            
            # Notificação em tempo real
            self.websocket_service.send_moderation_update(
                queue_item.comment.uuid,
                action,
                self.request.user.username
            )
            
        except Exception as e:
            messages.error(self.request, f'Erro ao executar ação: {str(e)}')
            return redirect('comments:moderation_detail', pk=queue_id)
        
        return redirect('comments:moderation_queue')
    
    def form_invalid(self, form):
        queue_id = self.kwargs.get('pk')
        messages.error(self.request, 'Dados inválidos')
        return redirect('comments:moderation_detail', pk=queue_id)


class BulkModerationView(LoginRequiredMixin, PermissionRequiredMixin,
                        ModerationServiceMixin, FormView):
    """
    View para moderação em massa
    """
    form_class = BulkModerationForm
    template_name = 'comments/moderation/bulk_action.html'
    permission_required = 'comments.moderate_comment'
    
    def form_valid(self, form):
        comment_ids = form.cleaned_data['comment_ids']
        action = form.cleaned_data['action']
        reason = form.cleaned_data['reason']
        
        try:
            if action == 'approve':
                results = self.moderation_service.bulk_approve_comments(
                    comment_ids,
                    self.request.user.id,
                    reason
                )
            elif action == 'reject':
                results = self.moderation_service.bulk_reject_comments(
                    comment_ids,
                    self.request.user.id,
                    reason
                )
            elif action == 'spam':
                results = self.moderation_service.bulk_mark_as_spam(
                    comment_ids,
                    self.request.user.id,
                    reason
                )
            
            success_count = results.get('success_count', 0)
            error_count = results.get('error_count', 0)
            
            if success_count > 0:
                messages.success(
                    self.request,
                    f'{success_count} comentários processados com sucesso'
                )
            
            if error_count > 0:
                messages.warning(
                    self.request,
                    f'{error_count} comentários não puderam ser processados'
                )
            
        except Exception as e:
            messages.error(self.request, f'Erro na moderação em massa: {str(e)}')
        
        return redirect('comments:moderation_queue')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comment_ids = self.request.GET.get('ids', '').split(',')
        context['selected_comments'] = Comment.objects.filter(
            id__in=[int(id_) for id_ in comment_ids if id_.isdigit()]
        )
        return context


class ModerationStatsView(LoginRequiredMixin, PermissionRequiredMixin,
                         ModerationServiceMixin, TemplateView):
    """
    View para estatísticas de moderação
    """
    template_name = 'comments/moderation/stats.html'
    permission_required = 'comments.moderate_comment'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estatísticas gerais
        context['general_stats'] = self.moderation_service.get_moderation_stats()
        
        # Estatísticas por moderador
        context['moderator_stats'] = self.moderation_service.get_moderator_stats(
            days=30
        )
        
        # Estatísticas de moderação automática
        context['auto_moderation_stats'] = self.moderation_service.get_auto_moderation_stats(
            days=30
        )
        
        # Tendências dos últimos 7 dias
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=7)
        
        daily_stats = []
        current_date = start_date
        while current_date <= end_date:
            day_stats = {
                'date': current_date,
                'pending': ModerationQueue.objects.filter(
                    created_at__date=current_date,
                    is_resolved=False
                ).count(),
                'approved': ModerationAction.objects.filter(
                    created_at__date=current_date,
                    action='approve'
                ).count(),
                'rejected': ModerationAction.objects.filter(
                    created_at__date=current_date,
                    action='reject'
                ).count(),
                'spam': ModerationAction.objects.filter(
                    created_at__date=current_date,
                    action='spam'
                ).count(),
            }
            daily_stats.append(day_stats)
            current_date += timedelta(days=1)
        
        context['daily_stats'] = daily_stats
        
        return context


class ModerationConfigView(LoginRequiredMixin, PermissionRequiredMixin,
                          ModerationServiceMixin, FormView):
    """
    View para configuração de moderação
    """
    form_class = CommentModerationConfigForm
    template_name = 'comments/moderation/config.html'
    success_url = reverse_lazy('comments:moderation_config')
    permission_required = 'comments.change_commentmoderation'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Tenta obter configuração existente ou cria uma nova
        try:
            config = CommentModeration.objects.get(
                content_type__isnull=True,
                object_id__isnull=True
            )
        except CommentModeration.DoesNotExist:
            config = CommentModeration()
        
        kwargs['instance'] = config
        return kwargs
    
    def form_valid(self, form):
        config = form.save(commit=False)
        config.content_type = None
        config.object_id = None
        config.save()
        
        messages.success(self.request, 'Configuração de moderação salva com sucesso')
        return super().form_valid(form)


class AssignModerationView(LoginRequiredMixin, PermissionRequiredMixin,
                          ModerationServiceMixin, FormView):
    """
    View para atribuir comentários a moderadores
    """
    permission_required = 'comments.moderate_comment'
    
    def post(self, request, *args, **kwargs):
        queue_id = kwargs.get('pk')
        moderator_id = request.POST.get('moderator_id')
        
        if not moderator_id:
            return JsonResponse({'error': 'Moderador não especificado'}, status=400)
        
        try:
            success = self.moderation_service.assign_to_moderator(
                queue_id,
                int(moderator_id)
            )
            
            if success:
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'error': 'Falha ao atribuir'}, status=400)
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class ModerationHistoryView(LoginRequiredMixin, PermissionRequiredMixin,
                           ListView):
    """
    View para histórico de moderação
    """
    model = ModerationAction
    template_name = 'comments/moderation/history.html'
    context_object_name = 'actions'
    paginate_by = 50
    permission_required = 'comments.view_moderationaction'
    
    def get_queryset(self):
        return ModerationAction.objects.select_related(
            'comment__author',
            'moderator'
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estatísticas do histórico
        total_actions = ModerationAction.objects.count()
        context['total_actions'] = total_actions
        
        context['action_counts'] = ModerationAction.objects.values(
            'action'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        return context


class SpamDetectionView(LoginRequiredMixin, PermissionRequiredMixin,
                       ModerationServiceMixin, TemplateView):
    """
    View para detecção de spam
    """
    template_name = 'comments/moderation/spam_detection.html'
    permission_required = 'comments.moderate_comment'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Comentários suspeitos de spam
        context['suspicious_comments'] = self.moderation_service.get_suspicious_comments(
            limit=50
        )
        
        # Estatísticas de spam
        context['spam_stats'] = {
            'total_spam': Comment.objects.filter(moderation_status='spam').count(),
            'auto_detected': ModerationAction.objects.filter(
                action='spam',
                moderator__isnull=True
            ).count(),
            'manual_marked': ModerationAction.objects.filter(
                action='spam',
                moderator__isnull=False
            ).count(),
        }
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Executa detecção automática de spam"""
        try:
            results = self.moderation_service.run_spam_detection()
            
            messages.success(
                request,
                f'Detecção executada: {results.get("detected_count", 0)} comentários marcados como spam'
            )
        except Exception as e:
            messages.error(request, f'Erro na detecção de spam: {str(e)}')
        
        return redirect('comments:spam_detection')


class ReportedCommentsView(LoginRequiredMixin, PermissionRequiredMixin,
                          ModerationServiceMixin, ListView):
    """
    View para comentários reportados
    """
    template_name = 'comments/moderation/reported.html'
    context_object_name = 'reported_comments'
    paginate_by = 20
    permission_required = 'comments.moderate_comment'
    
    def get_queryset(self):
        return self.moderation_service.get_reported_comments()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report_stats'] = {
            'total_reports': ModerationQueue.objects.filter(
                is_reported=True
            ).count(),
            'pending_reports': ModerationQueue.objects.filter(
                is_reported=True,
                is_resolved=False
            ).count(),
        }
        return context