"""
Middleware para redirecionar para setup na primeira instalação
"""

from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings
from pathlib import Path
import re


class SetupMiddleware:
    """
    Middleware que redireciona para o setup wizard na primeira instalação
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # URLs que não devem ser redirecionadas
        self.exempt_urls = [
            '/config/setup/',
            '/config/setup/api/',
            '/health/',
            '/static/',
            '/media/',
        ]
    
    def __call__(self, request):
        # Verificar se é primeira instalação
        if self.is_first_installation():
            # Verificar se a URL atual não está na lista de exceções
            if not self.is_exempt_url(request.path):
                print(f"SetupMiddleware: Redirecting {request.path} to setup wizard")
                # Redirecionar para setup
                return redirect('config:setup_wizard')
            else:
                print(f"SetupMiddleware: Allowing {request.path} (exempt)")
        
        response = self.get_response(request)
        return response
    
    def is_first_installation(self):
        """Verifica se é primeira instalação"""
        first_install_file = Path(settings.BASE_DIR) / '.first_install'
        return first_install_file.exists()
    
    def is_exempt_url(self, path):
        """Verifica se a URL está na lista de exceções"""
        # URLs que não devem ser redirecionadas para o wizard
        exempt_urls = [
            '/config/wizard/',
            '/config/wizard-teste/',
            '/config/setup/api/',
            '/config/setup-wizard/api/',
            '/config/setup/redirect/',
            '/admin/',
            '/accounts/login/',
            '/accounts/logout/',
            '/static/',
            '/media/',
        ]
        return any(path.startswith(url) for url in exempt_urls) 