from typing import Dict, Any
from django.http import HttpRequest
from apps.config.services.module_service import ModuleService
import logging

logger = logging.getLogger(__name__)

def modules_context(request: HttpRequest) -> Dict[str, Any]:
    """
    Context processor para adicionar informações de módulos a todos os templates.
    
    Adiciona:
    - available_modules: Lista de módulos habilitados que devem aparecer no menu
    - current_module: Informações do módulo atual baseado na URL
    """
    context = {}
    
    try:
        # Verificar se é primeira instalação
        from django.db import connection, OperationalError
        
        try:
            connection.ensure_connection()
        except (OperationalError, Exception):
            # Se não conseguir conectar ao banco, retornar contexto vazio
            return context
            
        # Inicializar o service de módulos
        module_service = ModuleService()
        
        # Adicionar módulos disponíveis para o menu
        available_modules = module_service.get_menu_modules()
        context['available_modules'] = available_modules
        
        # Identificar módulo atual baseado na URL
        current_app = _get_current_app(request)
        if current_app:
            current_module = module_service.get_module_by_name(current_app)
            context['current_module'] = current_module
        else:
            context['current_module'] = None
            
        logger.debug(f"Context processor: {len(available_modules)} módulos disponíveis")
        
    except Exception as e:
        logger.warning(f"Erro no context processor de módulos: {str(e)}")
        # Em caso de erro, retornar contexto vazio para não quebrar o site
        context = {
            'available_modules': [],
            'current_module': None
        }
    
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