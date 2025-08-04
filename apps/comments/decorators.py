from functools import wraps
from django.http import Http404
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from apps.config.services.module_service import ModuleService


def require_comments_module(view_func=None, *, redirect_url=None, raise_404=False):
    """
    Decorator que verifica se o módulo comments está ativo.
    
    Args:
        redirect_url: URL para redirecionar se o módulo estiver inativo
        raise_404: Se True, levanta Http404 em vez de redirecionar
    
    Usage:
        @require_comments_module
        def my_view(request):
            pass
            
        @require_comments_module(redirect_url='home')
        def my_view(request):
            pass
            
        @require_comments_module(raise_404=True)
        def my_view(request):
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            module_service = ModuleService()
            
            if not module_service.is_module_enabled('comments'):
                if raise_404:
                    raise Http404("Módulo de comentários não está disponível")
                
                messages.warning(
                    request, 
                    "O sistema de comentários não está disponível no momento."
                )
                
                if redirect_url:
                    return redirect(redirect_url)
                else:
                    # Redireciona para a página anterior ou home
                    return redirect(request.META.get('HTTP_REFERER', '/'))
            
            return func(request, *args, **kwargs)
        return wrapper
    
    if view_func is None:
        return decorator
    else:
        return decorator(view_func)


class CommentsModuleMixin:
    """
    Mixin para views que precisam verificar se o módulo comments está ativo.
    
    Usage:
        class MyView(CommentsModuleMixin, DetailView):
            comments_required = True  # Opcional, padrão é True
            comments_redirect_url = 'home'  # Opcional
    """
    comments_required = True
    comments_redirect_url = None
    
    def dispatch(self, request, *args, **kwargs):
        if self.comments_required:
            module_service = ModuleService()
            
            if not module_service.is_module_enabled('comments'):
                messages.warning(
                    request,
                    "O sistema de comentários não está disponível no momento."
                )
                
                if self.comments_redirect_url:
                    return redirect(self.comments_redirect_url)
                else:
                    return redirect(request.META.get('HTTP_REFERER', '/'))
        
        return super().dispatch(request, *args, **kwargs)