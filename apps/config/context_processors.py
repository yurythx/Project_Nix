from typing import Dict, Any
from django.http import HttpRequest
from apps.config.services.module_service import ModuleService
from pathlib import Path
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def is_first_installation() -> bool:
    """Verifica se é primeira instalação"""
    first_install_file = Path(settings.BASE_DIR) / '.first_install'
    return first_install_file.exists()

def can_access_database() -> bool:
    """Verifica se o banco de dados está acessível"""
    try:
        from django.db import connection
        connection.ensure_connection()
        return True
    except Exception:
        return False

def modules_context(request: HttpRequest) -> Dict[str, Any]:
    """Context processor principal para módulos"""
    context = {}
    
    # Verificação unificada de primeira instalação
    if is_first_installation():
        return context
    
    # Verificação robusta de banco
    if not can_access_database():
        return context
    
    try:
        service = ModuleService()
        available_modules = service.get_menu_modules()
        
        # Obter o app atual da requisição
        current_app = None
        if hasattr(request, 'resolver_match') and request.resolver_match:
            current_app = request.resolver_match.app_name or request.resolver_match.namespace
        
        # Buscar módulo atual usando get_module_by_name
        current_module = None
        if current_app:
            current_module = service.get_module_by_name(current_app)
        
        context.update({
            'available_modules': available_modules,
            'current_module': current_module,
            'modules_configured': bool(available_modules),
        })
    except Exception as e:
        logger.error(f"Erro no context processor de módulos: {e}")
        context['modules_configured'] = False
    
    return context

def _get_current_app(request: HttpRequest) -> str:
    """
    Identifica o app atual baseado na URL da requisição.
    """
    try:
        if hasattr(request, 'resolver_match') and request.resolver_match:
            namespace = request.resolver_match.namespace
            if namespace:
                # Remove prefixos como 'admin:' se existirem
                return namespace.split(':')[0] if ':' in namespace else namespace
        return None
    except Exception:
        return None