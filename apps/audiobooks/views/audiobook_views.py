from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.shortcuts import render
from django.db.models import Q
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from apps.audiobooks.models import VideoAudio, VideoProgress, VideoFavorite
from apps.audiobooks.forms.audiobook_form import VideoAudioForm


class VideoAudioListView(ListView):
    """Lista todos os vídeos disponíveis com opções de filtro e busca"""
    model = VideoAudio
    template_name = 'audiobooks/video_list.html'
    context_object_name = 'videos'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = VideoAudio.objects.filter(is_public=True)
        
        # Filtro por categoria
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
            
        # Filtro por busca
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(author__icontains=search_query) |
                Q(narrator__icontains=search_query)
            )
            
        # Ordenação
        sort_by = self.request.GET.get('sort_by', '-created_at')
        if sort_by in ['title', '-title', 'created_at', '-created_at']:
            queryset = queryset.order_by(sort_by)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = dict(VideoAudio.CATEGORY_CHOICES)
        context['current_category'] = self.request.GET.get('category', '')
        context['sort_by'] = self.request.GET.get('sort_by', '-created_at')
        context['search_query'] = self.request.GET.get('q', '')
        return context


class VideoAudioDetailView(DetailView):
    """Exibe os detalhes de um vídeo específico com player personalizado"""
    model = VideoAudio
    template_name = 'audiobooks/video_detail.html'
    context_object_name = 'video'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        video = self.get_object()
        
        # Verifica se o usuário já marcou este vídeo como favorito
        if self.request.user.is_authenticated:
            context['is_favorite'] = VideoFavorite.objects.filter(
                user=self.request.user, 
                video=video
            ).exists()
            
            # Obtém o progresso do usuário neste vídeo
            try:
                progress = VideoProgress.objects.get(
                    user=self.request.user,
                    video=video
                )
                context['user_progress'] = progress.current_time
                context['is_completed'] = progress.is_completed
            except VideoProgress.DoesNotExist:
                context['user_progress'] = 0
                context['is_completed'] = False
                
        # Recomenda vídeos relacionados (mesma categoria)
        related_videos = VideoAudio.objects.filter(
            category=video.category,
            is_public=True
        ).exclude(id=video.id)[:4]
        
        context['related_videos'] = related_videos
        return context


class VideoAudioCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """View para adicionar um novo vídeo"""
    model = VideoAudio
    form_class = VideoAudioForm  # TODO: Atualizar para VideoAudioForm
    template_name = 'audiobooks/video_form.html'
    success_url = reverse_lazy('audiobooks:video_list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
        
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, _('Vídeo adicionado com sucesso!'))
        return super().form_valid(form)


class VideoAudioUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View para editar um vídeo existente"""
    model = VideoAudio
    form_class = VideoAudioForm  # TODO: Atualizar para VideoAudioForm
    template_name = 'audiobooks/video_form.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
        
    def get_success_url(self):
        messages.success(self.request, _('Vídeo atualizado com sucesso!'))
        return reverse_lazy('audiobooks:video_detail', kwargs={'slug': self.object.slug})


class VideoAudioDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """View para excluir um vídeo"""
    model = VideoAudio
    template_name = 'audiobooks/video_confirm_delete.html'
    success_url = reverse_lazy('audiobooks:video_list')
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
        
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, _('Vídeo excluído com sucesso!'))
        return super().delete(request, *args, **kwargs)
