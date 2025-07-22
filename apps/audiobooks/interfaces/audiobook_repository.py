from abc import ABC, abstractmethod

class AudiobookRepositoryInterface(ABC):
    @abstractmethod
    def get_all(self):
        pass

    @abstractmethod
    def get_by_id(self, audiobook_id):
        pass

    @abstractmethod
    def create(self, data):
        pass

    @abstractmethod
    def update(self, audiobook_id, data):
        pass

    @abstractmethod
    def delete(self, audiobook_id):
        pass 