from django.views import View
from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

from apps.audiobooks.services.video_service import VideoAudioService
from apps.audiobooks.models import VideoAudio

class VideoListView(View):
    """
    View para listar vídeos com suporte a filtros e paginação
    """
    template_name = 'audiobooks/video_list.html'
    service_class = VideoAudioService
    paginate_by = 12
    
    def get(self, request):
        """Manipula requisições GET para listar vídeos"""
        service = self.service_class()
        
        # Obtém parâmetros de filtro
        search_query = request.GET.get('q', '')
        category = request.GET.get('category', '')
        sort_by = request.GET.get('sort_by', '-created_at')
        
        # Obtém todos os vídeos públicos
        videos = service.get_all_videos().filter(is_public=True)
        
        # Aplica filtros
        if search_query:
            videos = videos.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(author__icontains=search_query) |
                Q(narrator__icontains=search_query)
            )
            
        if category:
            videos = videos.filter(category=category)
        
        # Ordenação
        if sort_by in ['title', '-title', 'created_at', '-created_at']:
            videos = videos.order_by(sort_by)
        
        # Paginação
        paginator = Paginator(videos, self.paginate_by)
        page = request.GET.get('page')
        
        try:
            videos = paginator.page(page)
        except PageNotAnInteger:
            videos = paginator.page(1)
        except EmptyPage:
            videos = paginator.page(paginator.num_pages)
        
        # Contexto para o template
        context = {
            'videos': videos,
            'search_query': search_query,
            'current_category': category,
            'sort_by': sort_by,
            'categories': dict(VideoAudio.CATEGORY_CHOICES),
            'is_paginated': videos.has_other_pages(),
            'page_obj': videos,
        }
        
        return render(request, self.template_name, context)
