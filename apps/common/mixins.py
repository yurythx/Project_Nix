from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.core.cache import cache
from django.db.models import Q
from typing import Optional, Any, List
from apps.config.services.module_service import ModuleService


class SuccessMessageMixin:
    """Adiciona mensagem de sucesso ao contexto da view"""
    success_message = None
    def form_valid(self, form):
        response = super().form_valid(form)
        if self.success_message:
            from django.contrib import messages
            messages.success(self.request, self.success_message)
        return response 

class ModuleEnabledRequiredMixin:
    module_name = None  # Ex: 'apps.articles'

    def dispatch(self, request, *args, **kwargs):
        service = ModuleService()
        if not self.module_name:
            raise ValueError('Defina module_name no Mixin')
        if not service.is_module_enabled(self.module_name):
            raise Http404('Módulo inativo')
        return super().dispatch(request, *args, **kwargs) 


# ============================================================================
# NOVA ARQUITETURA DE PERMISSÕES REUTILIZÁVEL
# ============================================================================

class BasePermissionMixin(UserPassesTestMixin):
    """
    Mixin base para controle de permissões com cache inteligente.
    
    Esta classe serve como base para todos os mixins de permissão,
    fornecendo funcionalidades comuns como cache, logging e tratamento de erros.
    """
    
    # Configurações padrão
    permission_denied_message = "🚫 Acesso negado! Você não tem permissão para realizar esta ação."
    redirect_url = 'pages:home'
    cache_timeout = 300  # 5 minutos
    
    # Grupos permitidos por padrão
    allowed_groups = ['administrador', 'admin', 'editor']
    
    def test_func(self):
        """Verifica se o usuário tem permissões adequadas."""
        user = self.request.user
        
        if not user.is_authenticated:
            return False
        
        # Superuser sempre tem acesso
        if user.is_superuser:
            return True
        
        # Verifica permissões específicas
        return self._check_permissions(user)
    
    def _check_permissions(self, user) -> bool:
        """Verifica permissões específicas. Deve ser sobrescrito pelas subclasses."""
        # Por padrão, verifica grupos permitidos
        return self._has_allowed_group(user)
    
    def _has_allowed_group(self, user) -> bool:
        """Verifica se o usuário pertence a grupos permitidos com cache distribuído."""
        from core.cache_service import cache_service
        
        # Tenta obter do cache distribuído
        has_group = cache_service.get_user_groups(user.id, self.allowed_groups)
        
        if has_group is None:
            # Consulta ao banco se não estiver no cache
            query = Q()
            for group in self.allowed_groups:
                query |= Q(name__iexact=group)
            has_group = user.groups.filter(query).exists()
            
            # Armazena no cache distribuído
            cache_service.set_user_groups(user.id, self.allowed_groups, has_group, self.cache_timeout)
        
        return has_group
    
    def handle_no_permission(self):
        """Trata quando o usuário não tem permissão."""
        if not self.request.user.is_authenticated:
            messages.warning(
                self.request,
                '🔐 Para acessar esta funcionalidade, você precisa fazer login primeiro.'
            )
            return redirect('accounts:login')
        
        messages.error(self.request, self.permission_denied_message)
        return redirect(self.redirect_url)
    
    def log_access_attempt(self, user, success: bool, details: str = ""):
        """Log de tentativa de acesso para auditoria."""
        try:
            import logging
            logger = logging.getLogger(__name__)
            status = "SUCCESS" if success else "DENIED"
            logger.info(
                f"Permission check: User {user.username} - {status} - "
                f"Path: {self.request.path} - {details}"
            )
        except Exception:
            pass  # Não falha se o logging não funcionar


class StaffOrSuperuserRequiredMixin(BasePermissionMixin):
    """
    Mixin que verifica se o usuário é membro da equipe (staff) ou superusuário.
    
    Permite acesso para:
    - Superusuários
    - Usuários staff
    - Usuários dos grupos configurados
    """
    
    def _check_permissions(self, user) -> bool:
        """Verifica se o usuário é staff ou pertence aos grupos permitidos."""
        if user.is_staff:
            return True
        return self._has_allowed_group(user)


class BaseOwnerOrStaffMixin(StaffOrSuperuserRequiredMixin):
    """
    Mixin base para verificação de propriedade de objetos.
    
    Esta classe fornece a estrutura base para mixins que verificam
    se o usuário é o proprietário de um objeto específico.
    """
    
    def _get_owner(self, obj: Any) -> Optional[Any]:
        """
        Obtém o proprietário do objeto. Deve ser sobrescrito pelas classes filhas.
        
        Args:
            obj: O objeto para verificar a propriedade
            
        Returns:
            O usuário proprietário ou None se não encontrado
        """
        raise NotImplementedError("Subclasses devem implementar _get_owner")
    
    def _check_permissions(self, user) -> bool:
        """Verifica se o usuário é o proprietário do objeto ou tem permissão de staff."""
        # Se for staff ou superusuário, permite o acesso
        if super()._check_permissions(user):
            return True
        
        # Para outros usuários, verifica se é o proprietário
        try:
            obj = self.get_object()
            owner = self._get_owner(obj)
            has_access = owner == user if owner else False
            
            # Log da tentativa
            self.log_access_attempt(
                user, 
                has_access, 
                f"Object owner: {owner.username if owner else 'None'}"
            )
            
            return has_access
            
        except Exception as e:
            # Log do erro para debug
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Erro ao verificar propriedade do objeto: {str(e)}")
            
            # Log da tentativa falhada
            self.log_access_attempt(user, False, f"Error: {str(e)}")
            return False


class ReadOnlyMixin(BasePermissionMixin):
    """
    Mixin para views somente leitura - não requer permissões especiais.
    
    Permite acesso para qualquer usuário (autenticado ou não).
    """
    
    def test_func(self):
        """Sempre retorna True para permitir acesso público."""
        return True
    
    def handle_no_permission(self):
        """Nunca é chamado, mas implementado por segurança."""
        return redirect(self.redirect_url)


class CreatorRequiredMixin(StaffOrSuperuserRequiredMixin):
    """
    Mixin que requer que o usuário seja o criador do conteúdo.
    
    Mais restritivo que OwnerOrStaffMixin - nem mesmo staff pode acessar
    conteúdo de outros usuários (exceto superusuários).
    """
    
    permission_denied_message = "🚫 Acesso negado! Apenas o criador pode realizar esta ação."
    
    def _check_permissions(self, user) -> bool:
        """Verifica se o usuário é o criador do objeto."""
        # Superusuários sempre têm acesso
        if user.is_superuser:
            return True
        
        # Para outros usuários, verifica se é o criador
        try:
            obj = self.get_object()
            creator = getattr(obj, 'criado_por', None)
            has_access = creator == user if creator else False
            
            # Log da tentativa
            self.log_access_attempt(
                user, 
                has_access, 
                f"Object creator: {creator.username if creator else 'None'}"
            )
            
            return has_access
            
        except Exception as e:
            self.log_access_attempt(user, False, f"Error: {str(e)}")
            return False


# ============================================================================
# MIXINS ESPECÍFICOS POR MÓDULO
# ============================================================================

class ContentOwnerOrStaffMixin(BaseOwnerOrStaffMixin):
    """
    Mixin genérico para conteúdo que tem campo 'criado_por'.
    
    Pode ser usado em qualquer modelo que tenha um campo 'criado_por'
    apontando para o modelo User.
    """
    
    def _get_owner(self, obj):
        """Obtém o criador do conteúdo."""
        return getattr(obj, 'criado_por', None)


class AuthorOrStaffMixin(BaseOwnerOrStaffMixin):
    """
    Mixin para conteúdo que tem campo 'author'.
    
    Pode ser usado em modelos como Article que têm campo 'author'.
    """
    
    def _get_owner(self, obj):
        """Obtém o autor do conteúdo."""
        return getattr(obj, 'author', None)


# ============================================================================
# MIXINS DE CONVENIÊNCIA
# ============================================================================

class AdminRequiredMixin(StaffOrSuperuserRequiredMixin):
    """
    Mixin que verifica se o usuário tem permissões de administrador.
    
    Permite acesso para:
    - Superusuários
    - Usuários staff
    - Usuários do grupo 'administrador'
    - Usuários do grupo 'admin'
    """
    
    allowed_groups = ['administrador', 'admin']


class EditorOrAdminRequiredMixin(StaffOrSuperuserRequiredMixin):
    """
    Mixin para controle de acesso de editores e administradores.
    
    Permite acesso para:
    - Superusuários
    - Usuários staff
    - Usuários do grupo 'administrador'
    - Usuários do grupo 'admin'
    - Usuários do grupo 'editor'
    """
    
    allowed_groups = ['administrador', 'admin', 'editor']


class SuperuserRequiredMixin(BasePermissionMixin):
    """
    Mixin que verifica se o usuário é superusuário.
    
    Permite acesso apenas para superusuários.
    """
    
    permission_denied_message = "🚫 Acesso restrito! Apenas superusuários podem acessar esta funcionalidade."
    
    def _check_permissions(self, user) -> bool:
        """Testa se o usuário é superusuário."""
        return user.is_superuser


# ============================================================================
# DECORATORS PARA VIEWS BASEADAS EM FUNÇÃO
# ============================================================================

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


def content_owner_required(view_func):
    """
    Decorator para views que requerem que o usuário seja o proprietário do conteúdo.
    
    Usage:
        @content_owner_required
        def my_view(request, content_id):
            # view code here
    """
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, '🔐 Você precisa estar logado para acessar esta área.')
            return redirect('pages:home')
        
        # Verificar se é superusuário ou staff
        if request.user.is_superuser or request.user.is_staff:
            return view_func(request, *args, **kwargs)
        
        # Para outros usuários, verificar propriedade
        # Esta implementação é genérica - pode ser customizada por módulo
        messages.error(
            request, 
            '🚫 Acesso negado! Você só pode editar conteúdo que você criou.'
        )
        return redirect('accounts:profile')
    
    return wrapper


# ============================================================================
# HELPER MIXINS
# ============================================================================

class PermissionHelperMixin:
    """
    Mixin helper para verificações de permissão em templates.
    
    Adiciona informações de permissão ao contexto das views.
    """
    
    def get_context_data(self, **kwargs):
        """Adiciona informações de permissão ao contexto."""
        context = super().get_context_data(**kwargs)
        
        user = self.request.user
        context.update({
            'user_is_admin': self.user_is_admin(user),
            'user_is_superuser': user.is_superuser,
            'user_is_staff': user.is_staff,
            'user_groups': list(user.groups.values_list('name', flat=True)) if user.is_authenticated else [],
            'user_permissions': self.get_user_permissions(user),
        })
        
        return context
    
    def user_is_admin(self, user):
        """Verifica se o usuário é administrador."""
        if not user.is_authenticated:
            return False
        
        return (
            user.is_superuser or 
            user.is_staff or 
            user.groups.filter(name__iexact='administrador').exists() or
            user.groups.filter(name__iexact='admin').exists()
        )
    
    def get_user_permissions(self, user):
        """Retorna as permissões do usuário em formato de dicionário."""
        if not user.is_authenticated:
            return {}
        
        return {
            'is_superuser': user.is_superuser,
            'is_staff': user.is_staff,
            'is_admin': self.user_is_admin(user),
            'groups': list(user.groups.values_list('name', flat=True)),
            'permissions': list(user.get_all_permissions()),
        }


class ConfigPermissionMixin(AdminRequiredMixin):
    """
    Mixin específico para o módulo de configurações.
    
    Herda de AdminRequiredMixin e adiciona validações específicas.
    """
    
    def dispatch(self, request, *args, **kwargs):
        """Override do dispatch para adicionar logs de acesso."""
        # Verificar permissões primeiro
        if not self.test_func():
            return self.handle_no_permission()
        
        # Log de acesso (opcional)
        self.log_access_attempt(request.user, True, f"Config access: {request.path}")
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_client_ip(self, request):
        """Obtém o IP do cliente."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip 