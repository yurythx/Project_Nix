from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, DetailView, FormView, TemplateView, UpdateView
)
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from ..models import CommentNotification, NotificationPreference
from ..forms import NotificationPreferencesForm
from ..interfaces import INotificationService, IWebSocketService
from ..services import NotificationService, WebSocketService
from ..repositories import DjangoNotificationRepository


class NotificationServiceMixin:
    """
    Mixin para injeção de dependência dos serviços de notificação
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._notification_service = None
        self._websocket_service = None
    
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


class NotificationListView(LoginRequiredMixin, NotificationServiceMixin, ListView):
    """
    View para listar notificações do usuário
    """
    model = CommentNotification
    template_name = 'comments/notifications/list.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        """Retorna notificações do usuário atual"""
        queryset = CommentNotification.objects.filter(
            recipient=self.request.user
        ).select_related(
            'sender',
            'comment__author',
            'comment__content_type'
        ).order_by('-created_at')
        
        # Filtros
        notification_type = self.request.GET.get('type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        is_read = self.request.GET.get('read')
        if is_read == 'true':
            queryset = queryset.filter(is_read=True)
        elif is_read == 'false':
            queryset = queryset.filter(is_read=False)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estatísticas de notificações
        context['unread_count'] = self.notification_service.get_unread_count(
            self.request.user.id
        )
        
        context['notification_types'] = CommentNotification.NOTIFICATION_TYPES
        
        # Contadores por tipo
        context['type_counts'] = {}
        for type_code, type_name in CommentNotification.NOTIFICATION_TYPES:
            count = CommentNotification.objects.filter(
                recipient=self.request.user,
                notification_type=type_code,
                is_read=False
            ).count()
            context['type_counts'][type_code] = count
        
        return context


class NotificationDetailView(LoginRequiredMixin, NotificationServiceMixin, DetailView):
    """
    View para exibir detalhes de uma notificação
    """
    model = CommentNotification
    template_name = 'comments/notifications/detail.html'
    context_object_name = 'notification'
    
    def get_queryset(self):
        return CommentNotification.objects.filter(
            recipient=self.request.user
        ).select_related(
            'sender',
            'comment__author',
            'comment__content_type'
        )
    
    def get_object(self):
        obj = super().get_object()
        # Marca como lida automaticamente
        if not obj.is_read:
            self.notification_service.mark_as_read(
                self.request.user.id,
                obj.uuid
            )
        return obj


class MarkNotificationReadView(LoginRequiredMixin, NotificationServiceMixin, DetailView):
    """
    View para marcar notificação como lida via AJAX
    """
    model = CommentNotification
    
    def get_queryset(self):
        return CommentNotification.objects.filter(
            recipient=self.request.user
        )
    
    def post(self, request, *args, **kwargs):
        notification = self.get_object()
        
        try:
            success = self.notification_service.mark_as_read(
                request.user.id,
                notification.uuid
            )
            
            if success:
                # Atualiza contador em tempo real
                unread_count = self.notification_service.get_unread_count(
                    request.user.id
                )
                
                self.websocket_service.send_notification_count_update(
                    request.user.id,
                    unread_count
                )
                
                return JsonResponse({
                    'success': True,
                    'unread_count': unread_count
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Falha ao marcar como lida'
                }, status=400)
        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


class MarkAllNotificationsReadView(LoginRequiredMixin, NotificationServiceMixin, TemplateView):
    """
    View para marcar todas as notificações como lidas
    """
    
    def post(self, request, *args, **kwargs):
        try:
            count = self.notification_service.mark_all_as_read(
                request.user.id
            )
            
            # Atualiza contador em tempo real
            self.websocket_service.send_notification_count_update(
                request.user.id,
                0
            )
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'marked_count': count
                })
            else:
                messages.success(
                    request,
                    f'{count} notificações marcadas como lidas'
                )
                return redirect('comments:notification_list')
        
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=500)
            else:
                messages.error(request, f'Erro: {str(e)}')
                return redirect('comments:notification_list')


class DeleteNotificationView(LoginRequiredMixin, NotificationServiceMixin, DetailView):
    """
    View para deletar notificação
    """
    model = CommentNotification
    
    def get_queryset(self):
        return CommentNotification.objects.filter(
            recipient=self.request.user
        )
    
    def post(self, request, *args, **kwargs):
        notification = self.get_object()
        
        try:
            notification.delete()
            
            # Atualiza contador em tempo real
            unread_count = self.notification_service.get_unread_count(
                request.user.id
            )
            
            self.websocket_service.send_notification_count_update(
                request.user.id,
                unread_count
            )
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'unread_count': unread_count
                })
            else:
                messages.success(request, 'Notificação removida')
                return redirect('comments:notification_list')
        
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=500)
            else:
                messages.error(request, f'Erro: {str(e)}')
                return redirect('comments:notification_list')


class NotificationPreferencesView(LoginRequiredMixin, NotificationServiceMixin, UpdateView):
    """
    View para gerenciar preferências de notificação
    """
    model = NotificationPreference
    form_class = NotificationPreferencesForm
    template_name = 'comments/notifications/preferences.html'
    success_url = reverse_lazy('comments:notification_preferences')
    
    def get_object(self):
        """Obtém ou cria preferências do usuário"""
        obj, created = NotificationPreference.objects.get_or_create(
            user=self.request.user
        )
        return obj
    
    def form_valid(self, form):
        messages.success(self.request, 'Preferências salvas com sucesso')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estatísticas de notificações
        context['notification_stats'] = {
            'total_received': CommentNotification.objects.filter(
                recipient=self.request.user
            ).count(),
            'unread_count': self.notification_service.get_unread_count(
                self.request.user.id
            ),
            'last_7_days': CommentNotification.objects.filter(
                recipient=self.request.user,
                created_at__gte=timezone.now() - timedelta(days=7)
            ).count(),
        }
        
        return context


class NotificationStatsView(LoginRequiredMixin, NotificationServiceMixin, TemplateView):
    """
    View para estatísticas de notificações
    """
    template_name = 'comments/notifications/stats.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        user_id = self.request.user.id
        
        # Estatísticas gerais
        context['general_stats'] = {
            'total_notifications': CommentNotification.objects.filter(
                recipient_id=user_id
            ).count(),
            'unread_count': self.notification_service.get_unread_count(user_id),
            'read_count': CommentNotification.objects.filter(
                recipient_id=user_id,
                is_read=True
            ).count(),
        }
        
        # Estatísticas por tipo
        context['type_stats'] = []
        for type_code, type_name in CommentNotification.NOTIFICATION_TYPES:
            count = CommentNotification.objects.filter(
                recipient_id=user_id,
                notification_type=type_code
            ).count()
            
            unread_count = CommentNotification.objects.filter(
                recipient_id=user_id,
                notification_type=type_code,
                is_read=False
            ).count()
            
            context['type_stats'].append({
                'type': type_code,
                'name': type_name,
                'total': count,
                'unread': unread_count,
            })
        
        # Tendências dos últimos 30 dias
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        daily_stats = []
        current_date = start_date
        while current_date <= end_date:
            day_count = CommentNotification.objects.filter(
                recipient_id=user_id,
                created_at__date=current_date
            ).count()
            
            daily_stats.append({
                'date': current_date,
                'count': day_count,
            })
            current_date += timedelta(days=1)
        
        context['daily_stats'] = daily_stats
        
        # Remetentes mais ativos
        context['top_senders'] = self.notification_service.get_top_senders(
            user_id,
            limit=10
        )
        
        return context


class NotificationSummaryView(LoginRequiredMixin, NotificationServiceMixin, TemplateView):
    """
    View para resumo de notificações
    """
    template_name = 'comments/notifications/summary.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Resumo do usuário
        context['summary'] = self.notification_service.get_user_summary(
            self.request.user.id
        )
        
        # Notificações recentes não lidas
        context['recent_unread'] = CommentNotification.objects.filter(
            recipient=self.request.user,
            is_read=False
        ).select_related(
            'sender',
            'comment__author'
        ).order_by('-created_at')[:10]
        
        return context


class NotificationAPIView(LoginRequiredMixin, NotificationServiceMixin, TemplateView):
    """
    API para notificações (AJAX)
    """
    
    def get(self, request, *args, **kwargs):
        """Retorna notificações não lidas"""
        try:
            notifications = CommentNotification.objects.filter(
                recipient=request.user,
                is_read=False
            ).select_related(
                'sender',
                'comment__author'
            ).order_by('-created_at')[:10]
            
            data = {
                'notifications': [
                    {
                        'id': str(notif.uuid),
                        'type': notif.notification_type,
                        'message': notif.message,
                        'sender': notif.sender.username if notif.sender else None,
                        'created_at': notif.created_at.isoformat(),
                        'comment_id': str(notif.comment.uuid) if notif.comment else None,
                    }
                    for notif in notifications
                ],
                'unread_count': self.notification_service.get_unread_count(
                    request.user.id
                ),
            }
            
            return JsonResponse(data)
        
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)


class TestNotificationView(LoginRequiredMixin, NotificationServiceMixin, TemplateView):
    """
    View para testar notificações (desenvolvimento)
    """
    
    def post(self, request, *args, **kwargs):
        """Cria notificação de teste"""
        if not request.user.is_staff:
            return JsonResponse({
                'error': 'Acesso negado'
            }, status=403)
        
        try:
            notification_type = request.POST.get('type', 'reply')
            message = request.POST.get('message', 'Notificação de teste')
            
            # Cria notificação de teste
            notification = CommentNotification.objects.create(
                recipient=request.user,
                notification_type=notification_type,
                message=message,
                sender=request.user
            )
            
            # Envia via WebSocket
            self.websocket_service.send_realtime_notification(
                request.user.id,
                {
                    'id': str(notification.uuid),
                    'type': notification_type,
                    'message': message,
                    'created_at': notification.created_at.isoformat(),
                }
            )
            
            return JsonResponse({
                'success': True,
                'notification_id': str(notification.uuid)
            })
        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


class CleanupNotificationsView(LoginRequiredMixin, NotificationServiceMixin, TemplateView):
    """
    View para limpeza de notificações antigas
    """
    
    def post(self, request, *args, **kwargs):
        """Remove notificações antigas"""
        try:
            days = int(request.POST.get('days', 30))
            
            deleted_count = self.notification_service.cleanup_old_notifications(
                request.user.id,
                days
            )
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'deleted_count': deleted_count
                })
            else:
                messages.success(
                    request,
                    f'{deleted_count} notificações antigas removidas'
                )
                return redirect('comments:notification_list')
        
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=500)
            else:
                messages.error(request, f'Erro: {str(e)}')
                return redirect('comments:notification_list')