from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponseRedirect, Http404, JsonResponse

from apps.audiobooks.models import VideoAudio, VideoProgress, VideoFavorite
from apps.audiobooks.forms.audiobook_form import VideoAudioForm
from apps.audiobooks.services.video_service import VideoAudioService


class VideoAudioListView(ListView):
    """Lista todos os vídeos disponíveis com opções de filtro e busca
    
    Princípios SOLID aplicados:
    - Single Responsibility: Apenas responsável pela listagem de vídeos
    - Open/Closed: Extensível via herança
    - Dependency Inversion: Usa o serviço de vídeo em vez de acessar diretamente os modelos
    """
    model = VideoAudio
    template_name = 'audiobooks/video_list.html'
    context_object_name = 'videos'
    paginate_by = 12
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.video_service = VideoAudioService()
    
    def get_queryset(self):
        # Obtém todos os vídeos públicos através do serviço
        queryset = self.video_service.get_all_videos().filter(is_public=True)
        
        # Filtro por categoria
        category = self.request.GET.get('category')
        if category:
            queryset = self.video_service.get_videos_by_category(category)
            
        # Filtro por busca
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = self.video_service.search_videos(search_query)
            
        # Ordenação
        sort_by = self.request.GET.get('sort_by', '-created_at')
        if sort_by in ['title', '-title', 'created_at', '-created_at']:
            queryset = queryset.order_by(sort_by)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.audiobooks.models.category import Category
        context['categories'] = Category.objects.filter(is_active=True)
        context['current_category'] = self.request.GET.get('category', '')
        context['sort_by'] = self.request.GET.get('sort_by', '-created_at')
        context['search_query'] = self.request.GET.get('q', '')
        
        # Adiciona vídeos em destaque se estiver na página principal (sem filtros)
        if not self.request.GET.get('q') and not self.request.GET.get('category'):
            context['featured_videos'] = self.video_service.get_featured_videos(5)
            context['recent_videos'] = self.video_service.get_recent_videos(5)
            context['popular_videos'] = self.video_service.get_popular_videos(5)
            
        return context


class VideoAudioDetailView(DetailView):
    """Exibe os detalhes de um vídeo específico com player personalizado
    
    Princípios SOLID aplicados:
    - Single Responsibility: Apenas responsável pela exibição de detalhes de vídeos
    - Open/Closed: Extensível via herança
    - Dependency Inversion: Usa o serviço de vídeo em vez de acessar diretamente os modelos
    """
    model = VideoAudio
    template_name = 'audiobooks/video_detail.html'
    context_object_name = 'video'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.video_service = VideoAudioService()
    
    def get_object(self, queryset=None):
        # Usa o serviço para obter o vídeo por slug
        slug = self.kwargs.get(self.slug_url_kwarg)
        video = self.video_service.get_video_by_slug(slug)
        if not video:
            raise Http404(_("Vídeo não encontrado"))
        return video
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        video = self.get_object()
        
        # Incrementa visualizações
        video.views += 1
        video.save(update_fields=['views'])
        
        # Obtém estatísticas do vídeo
        context['video_stats'] = self.video_service.get_video_stats(video.id)
        
        # Verifica se o usuário está autenticado para obter informações personalizadas
        if self.request.user.is_authenticated:
            # Verifica se o vídeo é favorito
            user_favorites = self.video_service.get_user_favorites(self.request.user)
            context['is_favorite'] = video in user_favorites
            
            # Obtém o progresso do usuário
            user_progress = self.video_service.get_user_progress(self.request.user)
            progress_video = user_progress.filter(video=video).first()
            
            if progress_video:
                context['user_progress'] = progress_video.current_time
                context['is_completed'] = progress_video.is_completed
            else:
                context['user_progress'] = 0
                context['is_completed'] = False
        
        # Obtém vídeos relacionados
        context['related_videos'] = self.video_service.get_related_videos(video, 4)
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Processa requisições POST para atualizar progresso ou favoritos"""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Usuário não autenticado'}, status=401)
            
        video = self.get_object()
        action = request.POST.get('action')
        
        if action == 'update_progress':
            return self.update_progress(request, video)
        elif action == 'toggle_favorite':
            return self.toggle_favorite(request, video)
        
        return JsonResponse({'error': 'Ação inválida'}, status=400)
    
    def update_progress(self, request, video):
        """Atualiza o progresso do usuário no vídeo"""
        try:
            current_time = float(request.POST.get('current_time', 0))
            is_completed = request.POST.get('is_completed') == 'true'
            
            success = self.video_service.update_progress(
                request.user, 
                video.id, 
                current_time, 
                is_completed
            )
            
            if success:
                return JsonResponse({
                    'success': True,
                    'current_time': current_time,
                    'is_completed': is_completed
                })
            else:
                return JsonResponse({'error': 'Falha ao atualizar progresso'}, status=500)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Parâmetros inválidos'}, status=400)
    
    def toggle_favorite(self, request, video):
        """Adiciona ou remove o vídeo dos favoritos do usuário"""
        try:
            is_favorite = self.video_service.toggle_favorite(request.user, video.id)
            
            return JsonResponse({
                'success': True,
                'is_favorite': is_favorite
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class VideoAudioCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """View para adicionar um novo vídeo
    
    Princípios SOLID aplicados:
    - Single Responsibility: Apenas responsável pela criação de vídeos
    - Open/Closed: Extensível via herança
    - Dependency Inversion: Usa o serviço de vídeo em vez de acessar diretamente os modelos
    """
    model = VideoAudio
    form_class = VideoAudioForm
    template_name = 'audiobooks/video_form.html'
    success_url = reverse_lazy('audiobooks:video_list')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.video_service = VideoAudioService()

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
        
    def form_valid(self, form):
        try:
            # Em vez de salvar o formulário diretamente, usamos o serviço
            video_data = form.cleaned_data
            self.object = self.video_service.create_video(video_data, self.request.user)
            messages.success(self.request, _('Vídeo adicionado com sucesso!'))
            return HttpResponseRedirect(self.get_success_url())
        except ValueError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)


class VideoAudioUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View para editar um vídeo existente
    
    Princípios SOLID aplicados:
    - Single Responsibility: Apenas responsável pela atualização de vídeos
    - Open/Closed: Extensível via herança
    - Dependency Inversion: Usa o serviço de vídeo em vez de acessar diretamente os modelos
    """
    model = VideoAudio
    form_class = VideoAudioForm
    template_name = 'audiobooks/video_form.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.video_service = VideoAudioService()
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def form_valid(self, form):
        try:
            # Em vez de salvar o formulário diretamente, usamos o serviço
            video_data = form.cleaned_data
            self.object = self.video_service.update_video(
                self.get_object().id, 
                video_data, 
                self.request.user
            )
            messages.success(self.request, _('Vídeo atualizado com sucesso!'))
            return HttpResponseRedirect(self.get_success_url())
        except ValueError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)
        
    def get_success_url(self):
        return reverse_lazy('audiobooks:video_detail', kwargs={'slug': self.object.slug})


class VideoAudioDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """View para excluir um vídeo
    
    Princípios SOLID aplicados:
    - Single Responsibility: Apenas responsável pela exclusão de vídeos
    - Open/Closed: Extensível via herança
    - Dependency Inversion: Usa o serviço de vídeo em vez de acessar diretamente os modelos
    """
    model = VideoAudio
    template_name = 'audiobooks/video_confirm_delete.html'
    success_url = reverse_lazy('audiobooks:video_list')
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.video_service = VideoAudioService()

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
        
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        
        # Em vez de excluir diretamente, usamos o serviço
        if self.video_service.delete_video(self.object.id, self.request.user):
            messages.success(self.request, _('Vídeo excluído com sucesso!'))
        else:
            messages.error(self.request, _('Erro ao excluir o vídeo.'))
            
        return HttpResponseRedirect(success_url)
