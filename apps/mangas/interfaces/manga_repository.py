from abc import ABC, abstractmethod

class MangaRepositoryInterface(ABC):
    @abstractmethod
    def get_all(self):
        pass

    @abstractmethod
    def get_by_id(self, manga_id):
        pass

    @abstractmethod
    def create(self, data):
        pass

    @abstractmethod
    def update(self, manga_id, data):
        pass

    @abstractmethod
    def delete(self, manga_id):
        pass 