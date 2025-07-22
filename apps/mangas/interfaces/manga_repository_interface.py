from abc import ABC, abstractmethod

class MangaRepositoryInterface(ABC):
    @abstractmethod
    def list_mangas(self):
        pass
    @abstractmethod
    def get_manga_by_slug(self, slug):
        pass
    @abstractmethod
    def create_manga(self, data):
        pass
    @abstractmethod
    def update_manga(self, slug, data):
        pass
    @abstractmethod
    def delete_manga(self, slug):
        pass
    @abstractmethod
    def list_capitulos(self, manga):
        pass
    @abstractmethod
    def get_capitulo_by_slug(self, manga, capitulo_slug):
        pass
    @abstractmethod
    def create_capitulo(self, manga, data):
        pass
    @abstractmethod
    def update_capitulo(self, manga, capitulo_slug, data):
        pass
    @abstractmethod
    def delete_capitulo(self, manga, capitulo_slug):
        pass
    @abstractmethod
    def list_paginas(self, capitulo):
        pass
    @abstractmethod
    def get_pagina(self, capitulo, number):
        pass
    @abstractmethod
    def create_pagina(self, capitulo, data):
        pass
    @abstractmethod
    def update_pagina(self, capitulo, number, data):
        pass
    @abstractmethod
    def delete_pagina(self, capitulo, number):
        pass 