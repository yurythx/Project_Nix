from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from django.http import HttpRequest, HttpResponse

class IModuleAccessMiddleware(ABC):
    """Interface para middleware de controle de acesso a módulos"""
    
    @abstractmethod
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """
        Processa a requisição para verificar acesso ao módulo
        :param request: Requisição HTTP
        :return: HttpResponse se deve redirecionar, None se deve continuar
        """
        pass
    
    @abstractmethod
    def is_path_exempt(self, path: str) -> bool:
        """
        Verifica se um caminho está isento de verificação
        :param path: Caminho da URL
        :return: True se isento
        """
        pass
    
    @abstractmethod
    def extract_app_name(self, path: str) -> Optional[str]:
        """
        Extrai o nome do app da URL
        :param path: Caminho da URL
        :return: Nome do app ou None
        """
        pass

class IModuleContextMiddleware(ABC):
    """Interface para middleware de contexto de módulos"""
    
    @abstractmethod
    def process_template_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """
        Adiciona contexto de módulos ao template
        :param request: Requisição HTTP
        :param response: Resposta HTTP
        :return: Resposta modificada
        """
        pass
    
    @abstractmethod
    def get_current_app(self, request: HttpRequest) -> Optional[str]:
        """
        Identifica o app atual baseado na URL
        :param request: Requisição HTTP
        :return: Nome do app atual ou None
        """
        pass
    
    @abstractmethod
    def get_menu_modules(self) -> List[Any]:
        """
        Obtém módulos disponíveis para o menu
        :return: Lista de módulos
        """
        pass
    
    @abstractmethod
    def get_current_module(self, app_name: str) -> Optional[Any]:
        """
        Obtém informações do módulo atual
        :param app_name: Nome do app
        :return: Módulo atual ou None
        """
        pass

class IModuleService(ABC):
    """Interface para serviço de módulos (reutilizada do services.py)"""
    
    @abstractmethod
    def is_module_enabled(self, app_name: str) -> bool:
        """
        Verifica se um módulo está habilitado
        :param app_name: Nome do app
        :return: True se habilitado
        """
        pass
    
    @abstractmethod
    def is_core_module(self, app_name: str) -> bool:
        """
        Verifica se é um módulo principal
        :param app_name: Nome do app
        :return: True se for módulo principal
        """
        pass
    
    @abstractmethod
    def get_module_by_name(self, app_name: str) -> Optional[Any]:
        """
        Busca módulo por nome
        :param app_name: Nome do app
        :return: Módulo encontrado ou None
        """
        pass
    
    @abstractmethod
    def get_menu_modules(self) -> List[Any]:
        """
        Retorna módulos que devem aparecer no menu
        :return: Lista de módulos do menu
        """
        pass 