from django.urls import path
from django.views.generic import RedirectView
from django.urls import reverse_lazy

from apps.audiobooks.views.video_list_view import VideoListView
from apps.audiobooks.views.video_detail_view import VideoDetailView
from apps.audiobooks.views.audiobook_views import (
    VideoAudioCreateView, VideoAudioUpdateView, VideoAudioDeleteView
)

app_name = 'audiobooks'

urlpatterns = [
    # Redireciona URLs antigas para as novas
    path('audiolivros/', RedirectView.as_view(pattern_name='audiobooks:video_list', permanent=True)),
    path('audiolivros/novo/', RedirectView.as_view(pattern_name='audiobooks:video_create', permanent=True)),
    path('audiolivros/<slug:slug>/', RedirectView.as_view(pattern_name='audiobooks:video_detail', permanent=True)),
    path('audiolivros/<slug:slug>/editar/', RedirectView.as_view(pattern_name='audiobooks:video_edit', permanent=True)),
    path('audiolivros/<slug:slug>/deletar/', RedirectView.as_view(pattern_name='audiobooks:video_delete', permanent=True)),
    
    # Novas URLs para vídeos
    path('', VideoListView.as_view(), name='video_list'),
    path('novo/', VideoAudioCreateView.as_view(), name='video_create'),
    path('<slug:slug>/', VideoDetailView.as_view(), name='video_detail'),
    path('<slug:slug>/editar/', VideoAudioUpdateView.as_view(), name='video_edit'),
    path('<slug:slug>/deletar/', VideoAudioDeleteView.as_view(), name='video_delete'),
    
    # URLs para API/JavaScript
    path('api/progresso/<slug:slug>/', VideoDetailView.as_view(), name='video_progress'),
    path('api/favoritar/<slug:slug>/', VideoDetailView.as_view(), name='video_favorite'),
]
