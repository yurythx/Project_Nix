from apps.mangas.interfaces.manga_repository_interface import MangaRepositoryInterface
from apps.mangas.models.manga import Manga, Capitulo, Pagina
from django.shortcuts import get_object_or_404

class MangaRepository(MangaRepositoryInterface):
    def list_mangas(self):
        return Manga.objects.all()
    def get_manga_by_slug(self, slug):
        return get_object_or_404(Manga, slug=slug)
    def create_manga(self, data):
        return Manga.objects.create(**data)
    def update_manga(self, slug, data):
        manga = self.get_manga_by_slug(slug)
        for key, value in data.items():
            setattr(manga, key, value)
        manga.save()
        return manga
    def delete_manga(self, slug):
        manga = self.get_manga_by_slug(slug)
        manga.delete()
    def list_capitulos(self, manga):
        return manga.capitulos.all()
    def get_capitulo_by_slug(self, manga, capitulo_slug):
        return get_object_or_404(Capitulo, manga=manga, slug=capitulo_slug)
    def create_capitulo(self, manga, data):
        return Capitulo.objects.create(manga=manga, **data)
    def update_capitulo(self, manga, capitulo_slug, data):
        capitulo = self.get_capitulo_by_slug(manga, capitulo_slug)
        for key, value in data.items():
            setattr(capitulo, key, value)
        capitulo.save()
        return capitulo
    def delete_capitulo(self, manga, capitulo_slug):
        capitulo = self.get_capitulo_by_slug(manga, capitulo_slug)
        capitulo.delete()
    def list_paginas(self, capitulo):
        return capitulo.paginas.all()
    def get_pagina(self, capitulo, number):
        return get_object_or_404(Pagina, capitulo=capitulo, number=number)
    def create_pagina(self, capitulo, data):
        return Pagina.objects.create(capitulo=capitulo, **data)
    def update_pagina(self, capitulo, number, data):
        pagina = self.get_pagina(capitulo, number)
        for key, value in data.items():
            setattr(pagina, key, value)
        pagina.save()
        return pagina
    def delete_pagina(self, capitulo, number):
        pagina = self.get_pagina(capitulo, number)
        pagina.delete() 