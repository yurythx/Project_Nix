from abc import ABC, abstractmethod

class BookRepositoryInterface(ABC):
    @abstractmethod
    def get_all(self):
        pass

    @abstractmethod
    def get_by_id(self, book_id):
        pass

    @abstractmethod
    def create(self, data):
        pass

    @abstractmethod
    def update(self, book_id, data):
        pass

    @abstractmethod
    def delete(self, book_id):
        pass 