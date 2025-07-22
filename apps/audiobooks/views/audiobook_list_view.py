from django.views import View
from django.shortcuts import render
from apps.audiobooks.services.audiobook_service import AudiobookService

class AudiobookListView(View):
    template_name = 'audiobooks/audiobook_list.html'
    service_class = AudiobookService

    def get(self, request):
        service = self.service_class()
        audiobooks = service.list_audiobooks()
        return render(request, self.template_name, {'audiobooks': audiobooks}) 