from abc import ABC, abstractmethod

class IService(ABC):
    """Interface base para todos os serviços"""
    @abstractmethod
    def health_check(self) -> bool:
        pass 