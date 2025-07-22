from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect

# Importação condicional do django-ratelimit
try:
    from django_ratelimit.exceptions import Ratelimited
    RATELIMIT_AVAILABLE = True
except ImportError:
    RATELIMIT_AVAILABLE = False
    class Ratelimited(Exception):
        pass
from django.core.exceptions import PermissionDenied
from django.contrib.auth.views import redirect_to_login
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class AccessControlMiddleware:
    """
    Middleware para controlar acesso e fornecer feedback adequado
    quando usuários tentam acessar áreas restritas.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def process_exception(self, request, exception):
        """Processa exceções de permissão e fornece feedback adequado"""
        
        if isinstance(exception, PermissionDenied):
            return self.handle_permission_denied(request, exception)
        
        return None
    
    def handle_permission_denied(self, request, exception):
        """Trata exceções de permissão negada"""
        
        # Se não está logado
        if not request.user.is_authenticated:
            return self.handle_unauthenticated_access(request)
        
        # Se está logado mas não tem permissão
        return self.handle_unauthorized_access(request)
    
    def handle_unauthenticated_access(self, request):
        """Trata acesso de usuários não autenticados"""
        
        # Determinar o tipo de área que está tentando acessar
        path = request.path
        area_info = self.get_area_info(path)
        
        # Adicionar mensagem explicativa
        messages.warning(
            request,
            f'🔐 Para acessar {area_info["name"]}, você precisa fazer login primeiro. '
            f'Use seu e-mail ou nome de usuário para entrar.'
        )
        
        # Redirecionar para login com next parameter
        return redirect('pages:home')
    
    def handle_unauthorized_access(self, request):
        """Trata acesso de usuários autenticados sem permissão"""
        
        path = request.path
        area_info = self.get_area_info(path)
        
        # Mensagem específica baseada na área
        if area_info["type"] == "config":
            messages.error(
                request,
                f'🚫 Acesso negado! {area_info["name"]} é restrita a administradores. '
                f'Você precisa ser administrador, staff ou superusuário para acessar esta área.'
            )
        elif area_info["type"] == "admin":
            messages.error(
                request,
                f'🚫 Acesso negado! {area_info["name"]} requer permissões especiais. '
                f'Entre em contato com um administrador se precisar de acesso.'
            )
        else:
            messages.error(
                request,
                f'🚫 Acesso negado! Você não tem permissão para acessar {area_info["name"]}.'
            )
        
        # Log da tentativa de acesso
        logger.warning(
            f'Unauthorized access attempt: User {request.user.username} '
            f'tried to access {path} from IP {self.get_client_ip(request)}'
        )
        
        # Redirecionar para área apropriada
        if hasattr(request.user, 'get_absolute_url'):
            return redirect(request.user.get_absolute_url())
        else:
            return redirect('accounts:profile')
    
    def get_area_info(self, path):
        """Retorna informações sobre a área que está sendo acessada"""

        # Excluir arquivos estáticos e mídia
        if path.startswith('/static/') or path.startswith('/media/'):
            return {
                'name': 'arquivos estáticos',
                'type': 'static',
                'description': 'recursos do sistema'
            }

        area_mappings = {
            '/config/': {
                'name': 'o Painel de Configurações',
                'type': 'config',
                'description': 'área administrativa do sistema'
            },
            '/admin/': {
                'name': 'o Django Admin',
                'type': 'admin',
                'description': 'interface administrativa'
            },
            '/accounts/configuracoes/': {
                'name': 'as Configurações de Conta',
                'type': 'profile',
                'description': 'configurações pessoais'
            },
            '/accounts/perfil/': {
                'name': 'o Perfil',
                'type': 'profile',
                'description': 'página de perfil'
            }
        }
        
        # Verificar correspondências exatas primeiro
        for pattern, info in area_mappings.items():
            if path.startswith(pattern):
                return info
        
        # Padrões genéricos
        if path.startswith('/config/'):
            return {
                'name': 'esta área de Configurações',
                'type': 'config',
                'description': 'área administrativa'
            }
        elif path.startswith('/admin/'):
            return {
                'name': 'o Django Admin',
                'type': 'admin',
                'description': 'interface administrativa'
            }
        elif path.startswith('/accounts/'):
            return {
                'name': 'esta área de Conta',
                'type': 'profile',
                'description': 'área de usuário'
            }
        else:
            return {
                'name': 'esta área',
                'type': 'general',
                'description': 'área restrita'
            }
    
    def get_client_ip(self, request):
        """Obtém o IP do cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class LoginRedirectMiddleware:
    """
    Middleware para melhorar redirecionamentos após login
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Se é uma resposta de redirecionamento para login
        if (hasattr(response, 'status_code') and 
            response.status_code == 302 and 
            'login' in response.get('Location', '')):
            
            # Adicionar informações contextuais
            self.add_login_context(request)
        
        return response
    
    def add_login_context(self, request):
        """Adiciona contexto útil para a página de login"""
        
        # Armazenar informações na sessão para uso na página de login
        if not hasattr(request, 'session'):
            return
        
        request.session['login_context'] = {
            'attempted_path': request.get_full_path(),
            'attempted_area': self.get_area_name(request.path),
            'timestamp': str(timezone.now()) if 'timezone' in globals() else None
        }


def handle_403_error(request, exception=None):
    """
    View personalizada para erro 403 (Forbidden)
    """
    from django.shortcuts import render
    from django.http import HttpResponseForbidden
    
    # Determinar contexto do erro
    area_info = AccessControlMiddleware(None).get_area_info(request.path)
    
    context = {
        'area_name': area_info['name'],
        'area_type': area_info['type'],
        'area_description': area_info['description'],
        'user_is_authenticated': request.user.is_authenticated,
        'user_username': request.user.username if request.user.is_authenticated else None,
        'login_url': reverse('accounts:login'),
        'home_url': reverse('pages:home'),
        'profile_url': reverse('accounts:profile') if request.user.is_authenticated else None,
    }
    
    return HttpResponseForbidden(
        render(request, 'errors/403.html', context).content
    )


def handle_404_error(request, exception=None):
    """
    View personalizada para erro 404 (Not Found)
    """
    from django.shortcuts import render
    from django.http import HttpResponseNotFound
    
    context = {
        'requested_path': request.path,
        'user_is_authenticated': request.user.is_authenticated,
        'login_url': reverse('accounts:login'),
        'home_url': reverse('pages:home'),
        'profile_url': reverse('accounts:profile') if request.user.is_authenticated else None,
    }
    
    return HttpResponseNotFound(
        render(request, 'errors/404.html', context).content
    )


class RateLimitMiddleware:
    """
    Middleware para tratar exceções de rate limiting de forma elegante
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Ratelimited:
            # Adiciona mensagem de erro amigável
            messages.error(
                request,
                '⏰ Muitas tentativas em pouco tempo. Aguarde alguns minutos antes de tentar novamente.'
            )

            # Redireciona para a mesma página ou página anterior
            referer = request.META.get('HTTP_REFERER')
            if referer:
                return HttpResponseRedirect(referer)
            else:
                return redirect('pages:home')

class SmartRedirectMiddleware:
    """
    Middleware para redirecionamentos inteligentes baseados no contexto do usuário
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """Processa views antes da execução"""
        
        # Debug logs
        print(f"SmartRedirectMiddleware: Processing {request.path}")
        print(f"SmartRedirectMiddleware: First installation: {self.is_first_installation()}")
        print(f"SmartRedirectMiddleware: Is setup wizard: {self.is_setup_wizard(request.path)}")
        print(f"SmartRedirectMiddleware: Is restricted area: {self.is_restricted_area(request.path)}")
        print(f"SmartRedirectMiddleware: User authenticated: {request.user.is_authenticated}")
        
        # Verificar se é primeira instalação e permitir acesso ao wizard
        if self.is_first_installation() and self.is_setup_wizard(request.path):
            print("SmartRedirectMiddleware: Allowing setup wizard access")
            return None
        
        # Se é uma tentativa de acesso a área restrita
        if self.is_restricted_area(request.path):
            
            # Se não está logado
            if not request.user.is_authenticated:
                print("SmartRedirectMiddleware: Redirecting to login")
                return self.redirect_to_smart_login(request)
            
            # Se está logado mas pode não ter permissão
            # Deixa a view processar e tratar a permissão
        
        return None
    
    def is_first_installation(self):
        """Verifica se é primeira instalação"""
        from pathlib import Path
        from django.conf import settings
        first_install_file = Path(settings.BASE_DIR) / '.first_install'
        return first_install_file.exists()
    
    def is_setup_wizard(self, path):
        """Verifica se é o wizard de setup"""
        setup_paths = [
            '/config/setup/',
            '/config/setup/api/',
            '/config/wizard/',
            '/config/wizard-teste/',
            '/config/wizard-teste/api/',
            '/config/setup-wizard/',
            '/config/setup-wizard/api/',
            '/config/setup-wizard/api/finalize/',
        ]
        return any(path.startswith(setup_path) for setup_path in setup_paths)
    
    def is_restricted_area(self, path):
        """Verifica se o caminho é uma área restrita"""

        # Excluir arquivos estáticos e mídia
        if path.startswith('/static/') or path.startswith('/media/'):
            return False

        restricted_patterns = [
            '/config/',
            '/admin/',
            '/accounts/configuracoes/',
            '/accounts/perfil/',
        ]

        return any(path.startswith(pattern) for pattern in restricted_patterns)
    
    def redirect_to_smart_login(self, request):
        """Redireciona para login com contexto inteligente"""
        
        area_info = AccessControlMiddleware(None).get_area_info(request.path)
        
        # Mensagem contextual
        messages.info(
            request,
            f'🔐 Para acessar {area_info["name"]}, faça login com seu e-mail ou nome de usuário.'
        )
        
        # Redirecionar para login
        return redirect('accounts:login')
