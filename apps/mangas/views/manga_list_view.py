from django.views import View
from django.shortcuts import render
from apps.mangas.services.manga_service import MangaService

class MangaListView(View):
    template_name = 'mangas/manga_list.html'
    service_class = MangaService

    def get(self, request):
        service = self.service_class()
        mangas = service.list_mangas()
        return render(request, self.template_name, {'mangas': mangas}) 