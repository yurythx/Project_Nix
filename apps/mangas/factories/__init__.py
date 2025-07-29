"""
Factories para criação de services e repositories
"""

from .service_factory import ServiceFactory, service_factory, get_manga_service, get_manga_repository

__all__ = [
    'ServiceFactory',
    'service_factory', 
    'get_manga_service',
    'get_manga_repository'
]
