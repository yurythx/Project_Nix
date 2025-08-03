from django.urls import path
from django.views.generic import RedirectView
from django.urls import reverse_lazy

from apps.audiobooks.views.category_view import VideoCategoryView
from apps.audiobooks.views.audiobook_views import (
    VideoAudioListView, VideoAudioDetailView, VideoAudioCreateView, 
    VideoAudioUpdateView, VideoAudioDeleteView
)
from apps.audiobooks.views.category_views import (
    CategoryListView, CategoryDetailView, CategoryCreateView,
    CategoryUpdateView, CategoryDeleteView
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
    path('', VideoAudioListView.as_view(), name='video_list'),
    path('novo/', VideoAudioCreateView.as_view(), name='video_create'),
    path('categoria/<str:category>/', VideoCategoryView.as_view(), name='video_category'),
    path('<slug:slug>/', VideoAudioDetailView.as_view(), name='video_detail'),
    path('<slug:slug>/editar/', VideoAudioUpdateView.as_view(), name='video_edit'),
    path('<slug:slug>/deletar/', VideoAudioDeleteView.as_view(), name='video_delete'),
    
    # URLs para API/JavaScript
    path('api/progresso/<slug:slug>/', VideoAudioDetailView.as_view(), name='video_progress'),
    path('api/favoritar/<slug:slug>/', VideoAudioDetailView.as_view(), name='video_favorite'),
    
    # URLs para CRUD de categorias
    path('categorias/', CategoryListView.as_view(), name='category_list'),
    path('categorias/nova/', CategoryCreateView.as_view(), name='category_create'),
    path('categorias/<slug:slug>/', CategoryDetailView.as_view(), name='category_detail'),
    path('categorias/<slug:slug>/editar/', CategoryUpdateView.as_view(), name='category_update'),
    path('categorias/<slug:slug>/deletar/', CategoryDeleteView.as_view(), name='category_delete'),
]
