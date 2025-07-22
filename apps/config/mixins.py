from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.http import Http404


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin que verifica se o usuário tem permissões de administrador.
    
    Permite acesso para:
    - Superusuários
    - Usuários staff
    - Usuários do grupo 'administrador'
    """
    
    def test_func(self):
        """Testa se o usuário tem permissões de administrador"""
        user = self.request.user
        
        # Verificar se é superusuário
        if user.is_superuser:
            return True
        
        # Verificar se é staff
        if user.is_staff:
            return True
        
        # Verificar se pertence ao grupo 'administrador'
        if user.groups.filter(name__iexact='administrador').exists():
            return True
        
        # Verificar se pertence ao grupo 'admin'
        if user.groups.filter(name__iexact='admin').exists():
            return True
        
        return False
    
    def handle_no_permission(self):
        """Trata quando o usuário não tem permissão"""
        if not self.request.user.is_authenticated:
            # Mensagem específica para usuários não logados
            messages.warning(
                self.request,
                '🔐 Para acessar o Painel de Configurações, você precisa fazer login primeiro. '
                'Use seu e-mail ou nome de usuário para entrar.'
            )
            # Redireciona para login com next parameter
            return redirect('pages:home')

        # Se está logado mas não tem permissão
        user = self.request.user
        user_groups = list(user.groups.values_list('name', flat=True))

        # Mensagem detalhada baseada no status do usuário
        if user_groups:
            groups_text = ', '.join(user_groups)
            messages.error(
                self.request,
                f'🚫 Acesso negado! Seus grupos ({groups_text}) não têm permissão para acessar '
                f'o Painel de Configurações. Você precisa ser administrador, staff ou superusuário.'
            )
        else:
            messages.error(
                self.request,
                '🚫 Acesso negado! Você precisa ser administrador para acessar o Painel de Configurações. '
                'Grupos permitidos: administrador, admin, staff ou superusuário.'
            )

        # Log da tentativa de acesso
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            f'Unauthorized config access: User {user.username} (groups: {user_groups}) '
            f'tried to access {self.request.path}'
        )

        # Redireciona para perfil
        return redirect('accounts:profile')


class SuperuserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin que verifica se o usuário é superusuário.
    
    Permite acesso apenas para superusuários.
    """
    
    def test_func(self):
        """Testa se o usuário é superusuário"""
        return self.request.user.is_superuser
    
    def handle_no_permission(self):
        """Trata quando o usuário não tem permissão"""
        if not self.request.user.is_authenticated:
            messages.warning(
                self.request,
                '🔐 Para acessar esta funcionalidade restrita, você precisa fazer login primeiro. '
                'Use seu e-mail ou nome de usuário para entrar.'
            )
            return redirect('pages:home')

        # Mensagem específica para superusuários
        user = self.request.user
        if user.is_staff:
            messages.error(
                self.request,
                '🚫 Acesso restrito! Esta funcionalidade é exclusiva para superusuários. '
                'Sua conta staff não tem permissões suficientes.'
            )
        else:
            messages.error(
                self.request,
                '🚫 Acesso restrito! Apenas superusuários podem acessar esta funcionalidade. '
                'Entre em contato com um administrador se precisar de acesso.'
            )

        return redirect('accounts:profile')


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin que verifica se o usuário é staff.
    
    Permite acesso para:
    - Superusuários
    - Usuários staff
    """
    
    def test_func(self):
        """Testa se o usuário é staff ou superusuário"""
        user = self.request.user
        return user.is_staff or user.is_superuser
    
    def handle_no_permission(self):
        """Trata quando o usuário não tem permissão"""
        if not self.request.user.is_authenticated:
            messages.warning(
                self.request,
                '🔐 Para acessar esta área da equipe, você precisa fazer login primeiro. '
                'Use seu e-mail ou nome de usuário para entrar.'
            )
            return redirect('pages:home')

        messages.error(
            self.request,
            '🚫 Acesso negado! Você precisa ser membro da equipe (staff) ou superusuário '
            'para acessar esta área. Entre em contato com um administrador.'
        )

        return redirect('accounts:profile')


class ConfigPermissionMixin(AdminRequiredMixin):
    """
    Mixin específico para o módulo de configurações.
    
    Herda de AdminRequiredMixin e adiciona validações específicas.
    """
    
    def dispatch(self, request, *args, **kwargs):
        """Override do dispatch para adicionar logs de acesso"""
        # Verificar permissões primeiro
        if not self.test_func():
            return self.handle_no_permission()
        
        # Log de acesso (opcional)
        self.log_access(request)
        
        return super().dispatch(request, *args, **kwargs)
    
    def log_access(self, request):
        """Log de acesso ao módulo de configurações"""
        try:
            from apps.config.services.system_config_service import AuditLogService
            from apps.config.repositories.config_repository import DjangoAuditLogRepository
            
            audit_service = AuditLogService(DjangoAuditLogRepository())
            audit_service.log_user_activity(
                user=request.user,
                action='CONFIG_ACCESS',
                description=f'Acesso ao módulo de configurações: {request.path}',
                ip_address=self.get_client_ip(request)
            )
        except Exception:
            # Se houver erro no log, não impede o acesso
            pass
    
    def get_client_ip(self, request):
        """Obtém o IP do cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


def admin_required(view_func):
    """
    Decorator para views baseadas em função que requer permissões de administrador.
    
    Usage:
        @admin_required
        def my_view(request):
            # view code here
    """
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, '🔐 Você precisa estar logado para acessar esta área.')
            return redirect('pages:home')
        
        # Verificar permissões
        user = request.user
        has_permission = (
            user.is_superuser or 
            user.is_staff or 
            user.groups.filter(name__iexact='administrador').exists() or
            user.groups.filter(name__iexact='admin').exists()
        )
        
        if not has_permission:
            messages.error(
                request, 
                '🚫 Acesso negado! Você precisa ser administrador para acessar esta área.'
            )
            return redirect('accounts:profile')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def superuser_required(view_func):
    """
    Decorator para views baseadas em função que requer superusuário.
    
    Usage:
        @superuser_required
        def my_view(request):
            # view code here
    """
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, '🔐 Você precisa estar logado para acessar esta área.')
            return redirect('pages:home')
        
        if not request.user.is_superuser:
            messages.error(
                request, 
                '🚫 Acesso restrito! Apenas superusuários podem acessar esta funcionalidade.'
            )
            return redirect('accounts:profile')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


class PermissionHelperMixin:
    """
    Mixin helper para verificações de permissão em templates.
    """
    
    def get_context_data(self, **kwargs):
        """Adiciona informações de permissão ao contexto"""
        context = super().get_context_data(**kwargs)
        
        user = self.request.user
        context.update({
            'user_is_admin': self.user_is_admin(user),
            'user_is_superuser': user.is_superuser,
            'user_is_staff': user.is_staff,
            'user_groups': list(user.groups.values_list('name', flat=True)) if user.is_authenticated else [],
        })
        
        return context
    
    def user_is_admin(self, user):
        """Verifica se o usuário é administrador"""
        if not user.is_authenticated:
            return False
        
        return (
            user.is_superuser or 
            user.is_staff or 
            user.groups.filter(name__iexact='administrador').exists() or
            user.groups.filter(name__iexact='admin').exists()
        )
