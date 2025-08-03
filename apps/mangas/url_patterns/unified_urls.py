from django.urls import path
from apps.mangas.views.unified_views import (
    UnifiedMangaListView,
    UnifiedMangaDetailView,
    UnifiedMangaCreateView,
    manga_stats_api
)

app_name = 'mangas_unified'

urlpatterns = [
    path('', UnifiedMangaListView.as_view(), name='list'),
    path('<slug:slug>/', UnifiedMangaDetailView.as_view(), name='detail'),
    path('create/', UnifiedMangaCreateView.as_view(), name='create'),
    path('api/<slug:slug>/stats/', manga_stats_api, name='api_stats'),
]