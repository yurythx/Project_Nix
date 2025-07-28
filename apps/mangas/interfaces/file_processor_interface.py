from abc import ABC, abstractmethod
from typing import Tuple
from django.db.models import Model

class IFileProcessorService(ABC):
    """
    Interface para serviços de processamento de arquivos de mangá.
    
    Define o contrato que todas as implementações de processamento de arquivos
    devem seguir, garantindo a substituição de implementações sem afetar os consumidores.
    """
    
    @abstractmethod
    def process_chapter_file(self, chapter: Model, file) -> Tuple[bool, str]:
        """
        Processa um arquivo de capítulo e cria as páginas correspondentes.
        
        Args:
            chapter: Instância do modelo Capitulo
            file: Arquivo a ser processado (pode ser .zip, .rar, etc.)
            
        Returns:
            Tupla (success, message) indicando o resultado da operação
        """
        pass
