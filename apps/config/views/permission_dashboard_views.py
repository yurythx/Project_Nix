"""
Views para o dashboard de permissões e monitoramento do sistema.
"""
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from django.contrib.auth.models import User, Group
from django.utils import timezone
from datetime import timedelta
import json
from django.views import View

from apps.common.mixins import SuperuserRequiredMixin, PermissionHelperMixin
from core.cache_service import cache_service


class PermissionDashboardView(SuperuserRequiredMixin, PermissionHelperMixin, TemplateView):
    """
    Dashboard principal de permissões com estatísticas e métricas.
    """
    template_name = 'config/permission_dashboard.html'
    
    def get_context_data(self, **kwargs):
        """Adiciona dados do dashboard ao contexto."""
        context = super().get_context_data(**kwargs)
        
        # Estatísticas gerais
        context.update({
            'total_users': User.objects.count(),
            'total_groups': Group.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'staff_users': User.objects.filter(is_staff=True).count(),
            'superusers': User.objects.filter(is_superuser=True).count(),
        })
        
        # Estatísticas de grupos
        group_stats = Group.objects.annotate(
            user_count=Count('user')
        ).order_by('-user_count')[:10]
        context['group_stats'] = group_stats
        
        # Estatísticas de cache
        cache_stats = cache_service.get_cache_stats()
        context['cache_stats'] = cache_stats
        
        # Usuários recentes
        recent_users = User.objects.filter(
            date_joined__gte=timezone.now() - timedelta(days=7)
        ).order_by('-date_joined')[:5]
        context['recent_users'] = recent_users
        
        # Atividade de permissões (simulado)
        context['permission_activity'] = self._get_permission_activity()
        
        return context
    
    def _get_permission_activity(self):
        """Simula atividade de permissões (em produção, viria de logs reais)."""
        return {
            'total_checks_today': 1250,
            'denied_access_today': 45,
            'cache_hit_rate': 0.92,
            'avg_response_time': 0.005,  # segundos
        }


class UserPermissionsView(SuperuserRequiredMixin, PermissionHelperMixin, ListView):
    """
    Lista de usuários com suas permissões detalhadas.
    """
    model = User
    template_name = 'config/user_permissions.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def get_queryset(self):
        """Filtra e ordena os usuários."""
        queryset = User.objects.select_related().prefetch_related('groups', 'user_permissions')
        
        # Filtros
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        # Filtro por status
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        elif status == 'staff':
            queryset = queryset.filter(is_staff=True)
        elif status == 'superuser':
            queryset = queryset.filter(is_superuser=True)
        
        # Ordenação
        order_by = self.request.GET.get('order_by', '-date_joined')
        queryset = queryset.order_by(order_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Adiciona dados extras ao contexto."""
        context = super().get_context_data(**kwargs)
        
        # Estatísticas de filtros
        context['total_users'] = User.objects.count()
        context['active_users'] = User.objects.filter(is_active=True).count()
        context['staff_users'] = User.objects.filter(is_staff=True).count()
        context['superusers'] = User.objects.filter(is_superuser=True).count()
        
        # Grupos disponíveis para filtro
        context['groups'] = Group.objects.all()
        
        return context


class GroupPermissionsView(SuperuserRequiredMixin, PermissionHelperMixin, ListView):
    """
    Lista de grupos com suas permissões e membros.
    """
    model = Group
    template_name = 'config/group_permissions.html'
    context_object_name = 'groups'
    paginate_by = 15
    
    def get_queryset(self):
        """Filtra e ordena os grupos."""
        queryset = Group.objects.annotate(
            user_count=Count('user')
        ).prefetch_related('permissions')
        
        # Filtro por nome
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        # Ordenação
        order_by = self.request.GET.get('order_by', '-user_count')
        queryset = queryset.order_by(order_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Adiciona dados extras ao contexto."""
        context = super().get_context_data(**kwargs)
        
        # Estatísticas
        context['total_groups'] = Group.objects.count()
        context['total_users'] = User.objects.count()
        
        return context


class CacheManagementView(SuperuserRequiredMixin, PermissionHelperMixin, TemplateView):
    """
    View para gerenciar o cache do sistema de permissões.
    """
    template_name = 'config/cache_management.html'
    
    def get_context_data(self, **kwargs):
        """Adiciona dados do cache ao contexto."""
        context = super().get_context_data(**kwargs)
        
        # Estatísticas do cache
        cache_stats = cache_service.get_cache_stats()
        context['cache_stats'] = cache_stats
        
        # Informações do sistema
        context['system_info'] = {
            'django_version': self._get_django_version(),
            'python_version': self._get_python_version(),
            'cache_backend': cache_stats.get('backend', 'Unknown'),
        }
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Processa ações de gerenciamento do cache."""
        action = request.POST.get('action')
        
        if action == 'clear_all':
            success = cache_service.clear_all_cache()
            if success:
                messages.success(request, '✅ Cache limpo com sucesso!')
            else:
                messages.error(request, '❌ Erro ao limpar cache.')
        
        elif action == 'invalidate_user':
            user_id = request.POST.get('user_id')
            if user_id:
                success = cache_service.invalidate_user_cache(int(user_id))
                if success:
                    messages.success(request, f'✅ Cache do usuário {user_id} invalidado!')
                else:
                    messages.error(request, f'❌ Erro ao invalidar cache do usuário {user_id}.')
        
        elif action == 'invalidate_object':
            model_name = request.POST.get('model_name')
            object_id = request.POST.get('object_id')
            if model_name and object_id:
                success = cache_service.invalidate_object_cache(model_name, int(object_id))
                if success:
                    messages.success(request, f'✅ Cache do objeto {model_name}:{object_id} invalidado!')
                else:
                    messages.error(request, f'❌ Erro ao invalidar cache do objeto.')
        
        return self.get(request, *args, **kwargs)
    
    def _get_django_version(self):
        """Obtém a versão do Django."""
        try:
            import django
            return django.get_version()
        except:
            return 'Unknown'
    
    def _get_python_version(self):
        """Obtém a versão do Python."""
        import sys
        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


class PermissionAnalyticsView(SuperuserRequiredMixin, PermissionHelperMixin, TemplateView):
    """
    View para analytics e métricas de permissões.
    """
    template_name = 'config/permission_analytics.html'
    
    def get_context_data(self, **kwargs):
        """Adiciona dados de analytics ao contexto."""
        context = super().get_context_data(**kwargs)
        
        # Dados para gráficos
        context['user_activity'] = self._get_user_activity_data()
        context['permission_checks'] = self._get_permission_check_data()
        context['cache_performance'] = self._get_cache_performance_data()
        
        return context
    
    def _get_user_activity_data(self):
        """Gera dados de atividade de usuários."""
        # Simula dados de atividade (em produção, viria de logs reais)
        return {
            'labels': ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'],
            'datasets': [{
                'label': 'Usuários Ativos',
                'data': [120, 135, 142, 138, 156, 145, 132],
                'borderColor': 'rgb(75, 192, 192)',
                'backgroundColor': 'rgba(75, 192, 192, 0.2)',
            }]
        }
    
    def _get_permission_check_data(self):
        """Gera dados de verificações de permissão."""
        return {
            'labels': ['Permitido', 'Negado', 'Cache Hit', 'Cache Miss'],
            'datasets': [{
                'label': 'Verificações de Permissão',
                'data': [1250, 45, 1150, 100],
                'backgroundColor': [
                    'rgba(75, 192, 192, 0.8)',
                    'rgba(255, 99, 132, 0.8)',
                    'rgba(54, 162, 235, 0.8)',
                    'rgba(255, 205, 86, 0.8)',
                ],
            }]
        }
    
    def _get_cache_performance_data(self):
        """Gera dados de performance do cache."""
        return {
            'labels': ['0-1ms', '1-5ms', '5-10ms', '10-50ms', '50ms+'],
            'datasets': [{
                'label': 'Tempo de Resposta',
                'data': [850, 320, 150, 80, 20],
                'backgroundColor': 'rgba(153, 102, 255, 0.8)',
            }]
        }


# API Views para AJAX
class PermissionAPIView(SuperuserRequiredMixin, View):
    """
    API para operações de permissões via AJAX.
    """
    
    def get(self, request):
        """Retorna dados de permissões em formato JSON."""
        action = request.GET.get('action')
        
        if action == 'user_permissions':
            user_id = request.GET.get('user_id')
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                    permissions = self._get_user_permissions_data(user)
                    return JsonResponse({'success': True, 'data': permissions})
                except User.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Usuário não encontrado'})
        
        elif action == 'cache_stats':
            stats = cache_service.get_cache_stats()
            return JsonResponse({'success': True, 'data': stats})
        
        elif action == 'system_stats':
            stats = self._get_system_stats()
            return JsonResponse({'success': True, 'data': stats})
        
        return JsonResponse({'success': False, 'error': 'Ação não reconhecida'})
    
    def _get_user_permissions_data(self, user):
        """Obtém dados detalhados de permissões do usuário."""
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'date_joined': user.date_joined.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'groups': list(user.groups.values_list('name', flat=True)),
            'permissions': list(user.get_all_permissions()),
            'user_permissions': list(user.user_permissions.values_list('codename', flat=True)),
        }
    
    def _get_system_stats(self):
        """Obtém estatísticas gerais do sistema."""
        return {
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'total_groups': Group.objects.count(),
            'staff_users': User.objects.filter(is_staff=True).count(),
            'superusers': User.objects.filter(is_superuser=True).count(),
            'recent_users': User.objects.filter(
                date_joined__gte=timezone.now() - timedelta(days=7)
            ).count(),
        } 