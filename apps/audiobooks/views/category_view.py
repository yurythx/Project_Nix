from django.views.generic import ListView
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.utils.translation import gettext_lazy as _

from apps.audiobooks.models import VideoAudio
from apps.audiobooks.models.category import Category
from apps.audiobooks.services.video_service import VideoAudioService


class VideoCategoryView(ListView):
    """
    View para listar vídeos por categoria
    
    Princípios SOLID aplicados:
    - Single Responsibility: Apenas responsável pela listagem de vídeos por categoria
    - Open/Closed: Extensível via herança
    - Dependency Inversion: Usa o serviço de vídeo em vez de acessar diretamente os modelos
    """
    model = VideoAudio
    template_name = 'audiobooks/video_category.html'
    context_object_name = 'videos'
    paginate_by = 12
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.video_service = VideoAudioService()
        self.category = None
    
    def get_queryset(self):
        # Obtém a categoria da URL
        category_slug = self.kwargs.get('category')
        
        # Verifica se a categoria é válida
        try:
            self.category = Category.objects.get(slug=category_slug, is_active=True)
        except Category.DoesNotExist:
            raise Http404(_('Categoria não encontrada'))
            
        # Obtém os vídeos da categoria através do serviço
        queryset = self.video_service.get_videos_by_category(self.category)
        
        # Ordenação
        sort_by = self.request.GET.get('sort_by', '-created_at')
        if sort_by in ['title', '-title', 'created_at', '-created_at']:
            queryset = queryset.order_by(sort_by)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Adiciona informações da categoria ao contexto
        context['category_name'] = self.category.name
        context['category_slug'] = self.category.slug
        context['category_obj'] = self.category
        context['categories'] = Category.objects.filter(is_active=True)
        context['sort_by'] = self.request.GET.get('sort_by', '-created_at')
        
        return context