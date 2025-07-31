from django.views import View
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import FormMixin
from django.urls import reverse

from apps.audiobooks.services.video_service import VideoAudioService
from apps.audiobooks.forms import VideoAudioForm
from apps.audiobooks.models import VideoAudio, VideoProgress, VideoFavorite

class VideoDetailView(FormMixin, View):
    """
    View para exibir os detalhes de um vídeo e gerenciar interações
    """
    template_name = 'audiobooks/video_detail.html'
    form_class = VideoAudioForm
    service_class = VideoAudioService
    
    def get_success_url(self):
        return reverse('video_detail', kwargs={'slug': self.object.slug})
    
    def get_queryset(self):
        """Retorna o queryset base para buscar o vídeo"""
        return VideoAudio.objects.all()
    
    def get_context_data(self, **kwargs):
        """Adiciona dados adicionais ao contexto"""
        context = super().get_context_data(**kwargs)
        context['related_videos'] = self.get_related_videos()
        return context
    
    def get_related_videos(self):
        """Obtém vídeos relacionados (mesma categoria ou autor)."""
        return self.service_class().get_related_videos(self.object)
    
    def get(self, request, *args, **kwargs):
        # Display video details
        
        service = self.service_class()
        video_slug = self.kwargs.get('slug')
        
        # Obtém o vídeo
        video = get_object_or_404(self.get_queryset(), slug=video_slug)
        
        # Incrementa o contador de visualizações
        video.views += 1
        video.save(update_fields=['views'])
        
        # Obtém o progresso do usuário (se logado)
        progress = 0
        if request.user.is_authenticated:
            try:
                video_progress = VideoProgress.objects.get(user=request.user, video=video)
                progress = video_progress.current_time
            except VideoProgress.DoesNotExist:
                pass
        
        context = {
            'video': video,
            'progress': progress,
            'related_videos': service.get_related_videos(video)[:6],
            'is_owner': False,  # Removido campo created_by do modelo
            'is_favorite': VideoFavorite.objects.filter(user=request.user, video=video).exists() if request.user.is_authenticated else False,
        }
        
        # Adiciona o formulário para edição (se for o dono)
        if context['is_owner']:
            context['form'] = self.get_form()
        
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        # Update video details
        
        if not request.user.is_authenticated:
            return redirect('login')
            
        self.object = get_object_or_404(self.get_queryset(), slug=kwargs.get('slug'))
        
        # Verifica se o usuário está autenticado
        if not request.user.is_authenticated:
            messages.error(request, 'Você precisa estar autenticado para realizar esta ação.')
            return redirect('login')
        
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
    
    def form_valid(self, form):
        """Processa o formulário válido"""
        video = form.save()
        messages.success(self.request, 'Vídeo atualizado com sucesso!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Processa o formulário inválido"""
        messages.error(self.request, 'Por favor, corrija os erros abaixo.')
        return self.render_to_response(self.get_context_data(form=form))
