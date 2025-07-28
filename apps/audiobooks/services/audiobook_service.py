from typing import List, Dict, Any, Optional
from django.db.models import QuerySet
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from apps.audiobooks.interfaces.services import IAudiobookService
from apps.audiobooks.repositories.audiobook_repository import AudiobookRepository
from apps.audiobooks.models.audiobook import Audiobook

User = get_user_model()

class AudiobookService(IAudiobookService):
    """
    Service para operações de audiolivros
    
    Princípios SOLID aplicados:
    - Single Responsibility: Apenas operações de audiolivros
    - Dependency Inversion: Depende da interface IAudiobookService
    - Open/Closed: Extensível via herança
    """
    
    def __init__(self, repository: AudiobookRepository = None):
        """
        Inicializa o service com injeção de dependência
        
        :param repository: Repository para acesso a dados
        """
        self.repository = repository or AudiobookRepository()
    
    def get_all_audiobooks(self, limit: Optional[int] = None) -> QuerySet:
        """Obtém todos os audiolivros"""
        audiobooks = self.repository.get_all()
        if limit:
            audiobooks = audiobooks[:limit]
        return audiobooks
    
    def get_audiobook_by_slug(self, slug: str):
        """Obtém audiolivro por slug"""
        try:
            return self.repository.get_by_slug(slug)
        except ObjectDoesNotExist:
            return None
    
    def search_audiobooks(self, query: str) -> QuerySet:
        """Busca audiolivros por título"""
        return self.repository.search_by_title(query)
    
    def create_audiobook(self, audiobook_data: Dict[str, Any], created_by: User):
        """Cria um novo audiolivro"""
        # Validações de negócio
        if not audiobook_data.get('title'):
            raise ValueError("Título é obrigatório")
        
        # Adiciona usuário criador
        audiobook_data['created_by'] = created_by
        
        return self.repository.create(audiobook_data)
    
    def update_audiobook(self, audiobook_id: int, audiobook_data: Dict[str, Any], updated_by: User):
        """Atualiza um audiolivro"""
        # Validações de negócio
        if not audiobook_data.get('title'):
            raise ValueError("Título é obrigatório")
        
        # Adiciona usuário que atualizou
        audiobook_data['updated_by'] = updated_by
        
        return self.repository.update(audiobook_id, audiobook_data)
    
    def delete_audiobook(self, audiobook_id: int, deleted_by: User) -> bool:
        """Deleta um audiolivro"""
        try:
            return self.repository.delete(audiobook_id)
        except ObjectDoesNotExist:
            return False 