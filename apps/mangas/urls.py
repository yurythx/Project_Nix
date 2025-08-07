from django.urls import path
from apps.mangas.views.manga_views import (
    MangaListView, MangaDetailView, MangaCreateView, MangaUpdateView, MangaDeleteView,
    CapituloDetailView, CapituloCreateView, CapituloCompleteCreateView, CapituloUpdateView, CapituloDeleteView,
    PaginaCreateView, PaginaUpdateView, PaginaDeleteView
)
from apps.mangas.views.volume_views import VolumeCreateView, VolumeUpdateView, VolumeDeleteView, VolumeDetailView
from apps.mangas.views.volume_upload_views import VolumeUploadCreateView, VolumeUploadUpdateView
from apps.mangas.views.capitulo_views import capitulo_paginas_lazy
from .views.enhanced_upload_views import (
    EnhancedUploadView,
    EnhancedCapituloCreateView,
    UploadSessionAPIView,
    FileValidationAPIView,
    QualityAnalysisAPIView,
    UploadStatsAPIView
)
from .views.resumable_upload_views import (
    ResumableUploadSessionView,
    ResumableChunkUploadView,
    ResumableUploadFinalizeView,
    ResumableUploadChunksView
)
from django.urls import path, include
from django.views.generic import TemplateView

app_name = 'mangas'

# URLs unificadas (IMPORT DIRETO)
from apps.mangas.views.unified_views import (
    UnifiedMangaListView,
    UnifiedMangaDetailView, 
    UnifiedMangaCreateView,
    manga_stats_api
)

# URLs unificadas (CORRIGIDAS)
urlpatterns = [
    # URLs de Mangá
    path('', MangaListView.as_view(), name='manga_list'),
    path('novo/', MangaCreateView.as_view(), name='manga_create'),
    
    # Demonstração das Melhorias (DEVE VIR ANTES DO SLUG GENÉRICO)
    path('demo-melhorias/', TemplateView.as_view(template_name='mangas/demo_melhorias_simple.html'), name='demo_melhorias'),
    
    # Upload Aprimorado Global
    path('enhanced-upload/', EnhancedUploadView.as_view(), name='enhanced_upload'),
    
    # URLs unificadas
    path('unified/', UnifiedMangaListView.as_view(), name='unified_list'),
    path('unified/<slug:slug>/', UnifiedMangaDetailView.as_view(), name='unified_detail'),
    path('unified/create/', UnifiedMangaCreateView.as_view(), name='unified_create'),
    path('unified/api/<slug:slug>/stats/', manga_stats_api, name='unified_api_stats'),
    
    # APIs do sistema de upload aprimorado
    path('api/upload/session/', UploadSessionAPIView.as_view(), name='upload_session_api'),
    path('api/upload/validate/', FileValidationAPIView.as_view(), name='file_validation_api'),
    path('api/upload/quality/', QualityAnalysisAPIView.as_view(), name='quality_analysis_api'),
    path('api/upload/stats/', UploadStatsAPIView.as_view(), name='upload_stats_api'),
    
    # APIs do sistema de upload resumível
    path('api/resumable/session/', ResumableUploadSessionView.as_view(), name='resumable_session_api'),
    path('api/resumable/session/<str:session_id>/', ResumableUploadSessionView.as_view(), name='resumable_session_detail_api'),
    path('api/resumable/chunk/', ResumableChunkUploadView.as_view(), name='resumable_chunk_api'),
    path('api/resumable/session/<str:session_id>/finalize/', ResumableUploadFinalizeView.as_view(), name='resumable_finalize_api'),
    path('api/resumable/session/<str:session_id>/chunks/', ResumableUploadChunksView.as_view(), name='resumable_chunks_api'),
    
    path('<slug:slug>/', MangaDetailView.as_view(), name='manga_detail'),
    path('<slug:slug>/editar/', MangaUpdateView.as_view(), name='manga_edit'),
    path('<slug:slug>/deletar/', MangaDeleteView.as_view(), name='manga_delete'),
    
    # URLs de Volume
    path('<slug:manga_slug>/volume/novo/', VolumeCreateView.as_view(), name='volume_create'),
    path('<slug:manga_slug>/volume/upload/', VolumeUploadCreateView.as_view(), name='volume_upload'),
    path('<slug:manga_slug>/volume/<slug:volume_slug>/', VolumeDetailView.as_view(), name='volume_detail'),
    path('<slug:manga_slug>/volume/<slug:volume_slug>/editar/', VolumeUpdateView.as_view(), name='volume_edit'),
    path('<slug:manga_slug>/volume/<slug:volume_slug>/upload/', VolumeUploadUpdateView.as_view(), name='volume_upload_update'),
    path('<slug:manga_slug>/volume/<slug:volume_slug>/deletar/', VolumeDeleteView.as_view(), name='volume_delete'),
    
    # URLs de Capítulo
    path('<slug:manga_slug>/capitulo/novo/', CapituloCreateView.as_view(), name='capitulo_create'),
    path('<slug:manga_slug>/capitulo/completo/', CapituloCompleteCreateView.as_view(), name='capitulo_complete_create'),
    path('<slug:manga_slug>/capitulo/enhanced/', EnhancedUploadView.as_view(), name='capitulo_enhanced_create'),
    path('<slug:manga_slug>/capitulo/<slug:capitulo_slug>/', CapituloDetailView.as_view(), name='capitulo_detail'),
    path('<slug:manga_slug>/capitulo/<slug:capitulo_slug>/editar/', CapituloUpdateView.as_view(), name='capitulo_edit'),
    path('<slug:manga_slug>/capitulo/<slug:capitulo_slug>/deletar/', CapituloDeleteView.as_view(), name='capitulo_delete'),
    
    # URLs de Página
    path('<slug:manga_slug>/capitulo/<slug:capitulo_slug>/pagina/novo/', PaginaCreateView.as_view(), name='pagina_create'),
    path('<slug:manga_slug>/capitulo/<slug:capitulo_slug>/pagina/<int:pk>/editar/', PaginaUpdateView.as_view(), name='pagina_edit'),
    path('<slug:manga_slug>/capitulo/<slug:capitulo_slug>/pagina/<int:pk>/deletar/', PaginaDeleteView.as_view(), name='pagina_delete'),
    path('<slug:manga_slug>/capitulo/<slug:capitulo_slug>/paginas-lazy/', capitulo_paginas_lazy, name='capitulo_paginas_lazy'),
]
