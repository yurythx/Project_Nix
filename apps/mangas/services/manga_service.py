from apps.mangas.repositories.manga_repository import MangaRepository

class MangaService:
    def __init__(self, repository=None):
        self.repository = repository or MangaRepository()

    # Mangá
    def list_mangas(self):
        return self.repository.list_mangas()
    def get_manga(self, slug):
        return self.repository.get_manga_by_slug(slug)
    def create_manga(self, data):
        return self.repository.create_manga(data)
    def update_manga(self, slug, data):
        return self.repository.update_manga(slug, data)
    def delete_manga(self, slug):
        return self.repository.delete_manga(slug)

    # Capítulo
    def list_capitulos(self, manga):
        return self.repository.list_capitulos(manga)
    def get_capitulo(self, manga, capitulo_slug):
        return self.repository.get_capitulo_by_slug(manga, capitulo_slug)
    def create_capitulo(self, manga, data):
        return self.repository.create_capitulo(manga, data)
    def update_capitulo(self, manga, capitulo_slug, data):
        return self.repository.update_capitulo(manga, capitulo_slug, data)
    def delete_capitulo(self, manga, capitulo_slug):
        return self.repository.delete_capitulo(manga, capitulo_slug)

    # Página
    def list_paginas(self, capitulo):
        return self.repository.list_paginas(capitulo)
    def get_pagina(self, capitulo, number):
        return self.repository.get_pagina(capitulo, number)
    def create_pagina(self, capitulo, data):
        return self.repository.create_pagina(capitulo, data)
    def update_pagina(self, capitulo, number, data):
        return self.repository.update_pagina(capitulo, number, data)
    def delete_pagina(self, capitulo, number):
        return self.repository.delete_pagina(capitulo, number) 