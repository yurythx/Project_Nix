from django.urls import path
from apps.mangas.views.manga_views import (
    MangaListView, MangaDetailView, MangaCreateView, MangaUpdateView, MangaDeleteView,
    CapituloDetailView, CapituloCreateView, CapituloCompleteCreateView, CapituloUpdateView, CapituloDeleteView,
    PaginaCreateView, PaginaUpdateView, PaginaDeleteView
)
from apps.mangas.views.volume_views import VolumeCreateView, VolumeUpdateView, VolumeDeleteView, VolumeDetailView

app_name = 'mangas'

urlpatterns = [
    # Mangá
    path('', MangaListView.as_view(), name='manga_list'),
    path('novo/', MangaCreateView.as_view(), name='manga_create'),
    path('<slug:slug>/', MangaDetailView.as_view(), name='manga_detail'),
    path('<slug:slug>/editar/', MangaUpdateView.as_view(), name='manga_edit'),
    path('<slug:slug>/deletar/', MangaDeleteView.as_view(), name='manga_delete'),

    # Capítulo
    path('<slug:manga_slug>/capitulo/novo/', CapituloCreateView.as_view(), name='capitulo_create'),
    path('<slug:manga_slug>/capitulo/completo/', CapituloCompleteCreateView.as_view(), name='capitulo_complete_create'),
    path('<slug:manga_slug>/capitulo/<slug:capitulo_slug>/', CapituloDetailView.as_view(), name='capitulo_detail'),
    path('<slug:manga_slug>/capitulo/<slug:capitulo_slug>/editar/', CapituloUpdateView.as_view(), name='capitulo_edit'),
    path('<slug:manga_slug>/capitulo/<slug:capitulo_slug>/deletar/', CapituloDeleteView.as_view(), name='capitulo_delete'),

    # Página
    path('<slug:manga_slug>/capitulo/<slug:capitulo_slug>/pagina/novo/', PaginaCreateView.as_view(), name='pagina_create'),
    path('<slug:manga_slug>/capitulo/<slug:capitulo_slug>/pagina/<int:pk>/editar/', PaginaUpdateView.as_view(), name='pagina_edit'),
    path('<slug:manga_slug>/capitulo/<slug:capitulo_slug>/pagina/<int:pk>/deletar/', PaginaDeleteView.as_view(), name='pagina_delete'),
    
    # Volume
    path('<slug:manga_slug>/volume/novo/', VolumeCreateView.as_view(), name='volume_create'),
    path('<slug:manga_slug>/volume/<slug:volume_slug>/', VolumeDetailView.as_view(), name='volume_detail'),
    path('<slug:manga_slug>/volume/<slug:volume_slug>/editar/', VolumeUpdateView.as_view(), name='volume_edit'),
    path('<slug:manga_slug>/volume/<slug:volume_slug>/deletar/', VolumeDeleteView.as_view(), name='volume_delete'),
]
