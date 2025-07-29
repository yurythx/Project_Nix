"""
URLs para API REST do app mangas
Implementa roteamento RESTful com endpoints aninhados
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import MangaViewSet, CapituloViewSet, PaginaViewSet, CacheViewSet
from .monitoring_views import MonitoringViewSet

# Importação para nested routers
from rest_framework_nested import routers

# Router principal
router = DefaultRouter()
router.register(r'mangas', MangaViewSet, basename='manga')
router.register(r'cache', CacheViewSet, basename='cache')
router.register(r'monitoring', MonitoringViewSet, basename='monitoring')

# Routers aninhados para capítulos
mangas_router = routers.NestedDefaultRouter(router, r'mangas', lookup='manga')
mangas_router.register(r'chapters', CapituloViewSet, basename='manga-chapters')

# Routers aninhados para páginas
chapters_router = routers.NestedDefaultRouter(mangas_router, r'chapters', lookup='chapter')
chapters_router.register(r'pages', PaginaViewSet, basename='chapter-pages')

app_name = 'mangas-api'

urlpatterns = [
    # Endpoints principais
    path('', include(router.urls)),

    # Endpoints aninhados
    path('', include(mangas_router.urls)),
    path('', include(chapters_router.urls)),

    # Endpoints customizados
    path('mangas/<slug:slug>/stats/',
         MangaViewSet.as_view({'get': 'statistics'}),
         name='manga-statistics'),

    path('mangas/featured/',
         MangaViewSet.as_view({'get': 'featured'}),
         name='manga-featured'),

    path('mangas/search/',
         MangaViewSet.as_view({'get': 'search'}),
         name='manga-search'),
]

"""
Estrutura de URLs da API:

=== MANGÁS ===
GET    /api/mangas/                           - Lista mangás
POST   /api/mangas/                           - Cria mangá
GET    /api/mangas/{slug}/                    - Detalhes do mangá
PUT    /api/mangas/{slug}/                    - Atualiza mangá
DELETE /api/mangas/{slug}/                    - Remove mangá
GET    /api/mangas/{slug}/chapters/           - Lista capítulos do mangá
GET    /api/mangas/{slug}/statistics/         - Estatísticas do mangá
GET    /api/mangas/featured/                  - Mangás em destaque
GET    /api/mangas/search/?q=termo            - Busca mangás

=== CAPÍTULOS ===
GET    /api/mangas/{manga_slug}/chapters/                    - Lista capítulos
POST   /api/mangas/{manga_slug}/chapters/                    - Cria capítulo
GET    /api/mangas/{manga_slug}/chapters/{slug}/             - Detalhes do capítulo
PUT    /api/mangas/{manga_slug}/chapters/{slug}/             - Atualiza capítulo
DELETE /api/mangas/{manga_slug}/chapters/{slug}/             - Remove capítulo
GET    /api/mangas/{manga_slug}/chapters/{slug}/pages/       - Lista páginas do capítulo
GET    /api/mangas/{manga_slug}/chapters/{slug}/navigation/  - Navegação do capítulo

=== PÁGINAS ===
GET    /api/mangas/{manga_slug}/chapters/{chapter_slug}/pages/     - Lista páginas
GET    /api/mangas/{manga_slug}/chapters/{chapter_slug}/pages/{id}/ - Detalhes da página

=== CACHE (Staff apenas) ===
GET    /api/cache/                            - Estatísticas do cache
POST   /api/cache/clear/                      - Limpa todo o cache
POST   /api/cache/invalidate_manga/           - Invalida cache de mangá específico

=== FILTROS E BUSCA ===
Parâmetros disponíveis:
- ?author=nome                 - Filtra por autor
- ?status=published            - Filtra por status
- ?is_featured=true            - Filtra mangás em destaque
- ?search=termo                - Busca em título, descrição e autor
- ?ordering=created_at         - Ordena por campo
- ?page=1                      - Paginação

Exemplos:
GET /api/mangas/?author=Oda&is_featured=true&ordering=-view_count
GET /api/mangas/one-piece/chapters/?page=2
GET /api/mangas/search/?q=naruto
"""
