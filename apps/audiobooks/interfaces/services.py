from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from django.db.models import QuerySet
from django.contrib.auth import get_user_model

User = get_user_model()

class IAudiobookService(ABC):
    """Interface para serviços de audiolivros"""
    
    @abstractmethod
    def get_all_audiobooks(self, limit: Optional[int] = None) -> QuerySet:
        """
        Obtém todos os audiolivros
        :param limit: Limite de resultados
        :return: QuerySet de audiolivros
        """
        pass
    
    @abstractmethod
    def get_audiobook_by_slug(self, slug: str):
        """
        Obtém audiolivro por slug
        :param slug: Slug do audiolivro
        :return: Audiolivro encontrado
        """
        pass
    
    @abstractmethod
    def search_audiobooks(self, query: str) -> QuerySet:
        """
        Busca audiolivros por título
        :param query: Termo de busca
        :return: QuerySet de audiolivros encontrados
        """
        pass
    
    @abstractmethod
    def create_audiobook(self, audiobook_data: Dict[str, Any], created_by: User):
        """
        Cria um novo audiolivro
        :param audiobook_data: Dados do audiolivro
        :param created_by: Usuário que está criando
        :return: Audiolivro criado
        """
        pass
    
    @abstractmethod
    def update_audiobook(self, audiobook_id: int, audiobook_data: Dict[str, Any], updated_by: User):
        """
        Atualiza um audiolivro
        :param audiobook_id: ID do audiolivro
        :param audiobook_data: Dados para atualização
        :param updated_by: Usuário que está atualizando
        :return: Audiolivro atualizado
        """
        pass
    
    @abstractmethod
    def delete_audiobook(self, audiobook_id: int, deleted_by: User) -> bool:
        """
        Deleta um audiolivro
        :param audiobook_id: ID do audiolivro
        :param deleted_by: Usuário que está deletando
        :return: True se deletado com sucesso
        """
        pass 