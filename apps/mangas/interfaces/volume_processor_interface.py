from abc import ABC, abstractmethod
from typing import Tuple
from django.db.models import Model

class IVolumeProcessorService(ABC):
    """
    Interface para serviços de processamento de arquivos de volumes de mangá.
    
    Define o contrato que todas as implementações de processamento de volumes
    devem seguir, garantindo a substituição de implementações sem afetar os consumidores.
    """
    
    @abstractmethod
    def process_volume_file(self, volume: Model, file_path: str) -> Tuple[bool, str]:
        """
        Processa um arquivo de volume e cria as páginas correspondentes.
        
        Args:
            volume: Instância do modelo Volume
            file_path: Caminho para o arquivo a ser processado (pode ser .zip, .rar, .7z, .pdf)
            
        Returns:
            Tupla (success, message) indicando o resultado da operação
        """
        pass
