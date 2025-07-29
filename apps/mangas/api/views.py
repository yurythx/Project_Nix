"""
ViewSets para API REST do app mangas
Implementa endpoints completos com autenticação e permissões
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.shortcuts import get_object_or_404

from ..models.manga import Manga
from ..models.volume import Volume
from ..models.capitulo import Capitulo
from ..models.pagina import Pagina
from ..serializers import (
    MangaListSerializer, MangaDetailSerializer, MangaCreateSerializer,
    VolumeSerializer, CapituloListSerializer, CapituloDetailSerializer,
    CapituloCreateSerializer, PaginaSerializer, PaginaCreateSerializer
)
from ..services.manga_service_simple import SimpleMangaService
from ..services.cache_service import manga_cache
from ..exceptions import MangaNotFoundError


class MangaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para mangás com funcionalidades completas
    
    Endpoints:
    - GET /api/mangas/ - Lista mangás
    - GET /api/mangas/{slug}/ - Detalhes do mangá
    - POST /api/mangas/ - Cria mangá (autenticado)
    - PUT/PATCH /api/mangas/{slug}/ - Atualiza mangá (autor/staff)
    - DELETE /api/mangas/{slug}/ - Remove mangá (autor/staff)
    """
    
    queryset = Manga.objects.filter(is_published=True)
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['author', 'status', 'is_featured']
    search_fields = ['title', 'description', 'author']
    ordering_fields = ['created_at', 'updated_at', 'view_count', 'title']
    ordering = ['-created_at']
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manga_service = SimpleMangaService()
    
    def get_serializer_class(self):
        """Retorna serializer apropriado para cada ação"""
        if self.action == 'list':
            return MangaListSerializer
        elif self.action == 'retrieve':
            return MangaDetailSerializer
        elif self.action == 'create':
            return MangaCreateSerializer
        return MangaDetailSerializer
    
    def get_permissions(self):
        """Define permissões por ação"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticatedOrReadOnly]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Otimiza queryset baseado na ação"""
        queryset = super().get_queryset()
        
        if self.action == 'list':
            # Para listagem, otimiza com select_related
            queryset = queryset.select_related('created_by').prefetch_related('volumes')
        elif self.action == 'retrieve':
            # Para detalhes, carrega tudo
            queryset = queryset.select_related('created_by').prefetch_related(
                'volumes__capitulos__paginas'
            )
        
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        """Recupera mangá com incremento de views"""
        instance = self.get_object()
        
        # Incrementa views de forma assíncrona
        self.manga_service.increment_manga_views(instance.id)
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def chapters(self, request, slug=None):
        """
        Retorna capítulos do mangá
        
        GET /api/mangas/{slug}/chapters/
        """
        manga = self.get_object()
        chapters = self.manga_service.get_manga_chapters(manga.slug)
        
        # Paginação
        page = self.paginate_queryset(chapters)
        if page is not None:
            serializer = CapituloListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = CapituloListSerializer(chapters, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, slug=None):
        """
        Retorna estatísticas do mangá
        
        GET /api/mangas/{slug}/statistics/
        """
        manga = self.get_object()
        context = self.manga_service.get_manga_context(manga)
        
        stats = {
            'total_volumes': len(context.get('volumes', [])),
            'total_chapters': context.get('total_chapters', 0),
            'view_count': manga.view_count,
            'latest_chapter': context.get('latest_chapter'),
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """
        Retorna mangás em destaque
        
        GET /api/mangas/featured/
        """
        featured_mangas = self.manga_service.get_featured_mangas(limit=10)
        serializer = MangaListSerializer(featured_mangas, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Busca mangás por termo
        
        GET /api/mangas/search/?q=termo
        """
        query = request.query_params.get('q', '')
        if not query:
            return Response({'error': 'Parâmetro q é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)
        
        results = self.manga_service.search_mangas(query)
        
        # Paginação
        page = self.paginate_queryset(results)
        if page is not None:
            serializer = MangaListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = MangaListSerializer(results, many=True, context={'request': request})
        return Response(serializer.data)


class CapituloViewSet(viewsets.ModelViewSet):
    """
    ViewSet para capítulos
    
    Endpoints aninhados em mangás:
    - GET /api/mangas/{manga_slug}/chapters/ - Lista capítulos
    - GET /api/mangas/{manga_slug}/chapters/{chapter_slug}/ - Detalhes do capítulo
    """
    
    serializer_class = CapituloDetailSerializer
    lookup_field = 'slug'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manga_service = SimpleMangaService()
    
    def get_queryset(self):
        """Filtra capítulos por mangá"""
        manga_slug = self.kwargs.get('manga_slug')
        if manga_slug:
            return Capitulo.objects.filter(
                volume__manga__slug=manga_slug,
                is_published=True
            ).select_related('volume__manga').prefetch_related('paginas')
        return Capitulo.objects.none()
    
    def get_serializer_class(self):
        """Retorna serializer apropriado"""
        if self.action == 'list':
            return CapituloListSerializer
        elif self.action == 'create':
            return CapituloCreateSerializer
        return CapituloDetailSerializer
    
    def retrieve(self, request, *args, **kwargs):
        """Recupera capítulo com incremento de views"""
        instance = self.get_object()
        
        # Incrementa views
        self.manga_service.increment_manga_views(instance.volume.manga.id)
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def pages(self, request, manga_slug=None, slug=None):
        """
        Retorna páginas do capítulo
        
        GET /api/mangas/{manga_slug}/chapters/{slug}/pages/
        """
        chapter = self.get_object()
        pages = chapter.paginas.all().order_by('number')
        
        serializer = PaginaSerializer(pages, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def navigation(self, request, manga_slug=None, slug=None):
        """
        Retorna informações de navegação do capítulo
        
        GET /api/mangas/{manga_slug}/chapters/{slug}/navigation/
        """
        chapter = self.get_object()
        context = self.manga_service.get_chapter_context(chapter)
        
        navigation = {
            'previous_chapter': None,
            'next_chapter': None,
        }
        
        if context.get('previous_chapter'):
            prev_ch = context['previous_chapter']
            navigation['previous_chapter'] = {
                'id': prev_ch.id,
                'slug': prev_ch.slug,
                'title': prev_ch.title,
                'number': prev_ch.number,
            }
        
        if context.get('next_chapter'):
            next_ch = context['next_chapter']
            navigation['next_chapter'] = {
                'id': next_ch.id,
                'slug': next_ch.slug,
                'title': next_ch.title,
                'number': next_ch.number,
            }
        
        return Response(navigation)


class PaginaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para páginas (somente leitura)
    
    Endpoints aninhados em capítulos:
    - GET /api/mangas/{manga_slug}/chapters/{chapter_slug}/pages/ - Lista páginas
    - GET /api/mangas/{manga_slug}/chapters/{chapter_slug}/pages/{id}/ - Detalhes da página
    """
    
    serializer_class = PaginaSerializer
    
    def get_queryset(self):
        """Filtra páginas por capítulo"""
        manga_slug = self.kwargs.get('manga_slug')
        chapter_slug = self.kwargs.get('chapter_slug')
        
        if manga_slug and chapter_slug:
            return Pagina.objects.filter(
                capitulo__slug=chapter_slug,
                capitulo__volume__manga__slug=manga_slug,
                capitulo__is_published=True
            ).select_related('capitulo__volume__manga').order_by('number')
        
        return Pagina.objects.none()


class CacheViewSet(viewsets.ViewSet):
    """
    ViewSet para gerenciamento de cache (apenas staff)
    """
    
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """
        Retorna estatísticas do cache
        
        GET /api/cache/
        """
        if not request.user.is_staff:
            return Response({'error': 'Acesso negado'}, status=status.HTTP_403_FORBIDDEN)
        
        stats = manga_cache.get_cache_stats()
        return Response(stats)
    
    @action(detail=False, methods=['post'])
    def clear(self, request):
        """
        Limpa todo o cache
        
        POST /api/cache/clear/
        """
        if not request.user.is_staff:
            return Response({'error': 'Acesso negado'}, status=status.HTTP_403_FORBIDDEN)
        
        success = manga_cache.clear_all_cache()
        if success:
            return Response({'message': 'Cache limpo com sucesso'})
        else:
            return Response({'error': 'Erro ao limpar cache'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def invalidate_manga(self, request):
        """
        Invalida cache de um mangá específico
        
        POST /api/cache/invalidate_manga/
        Body: {"slug": "manga-slug"}
        """
        if not request.user.is_staff:
            return Response({'error': 'Acesso negado'}, status=status.HTTP_403_FORBIDDEN)
        
        slug = request.data.get('slug')
        if not slug:
            return Response({'error': 'Slug é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)
        
        success = manga_cache.invalidate_manga_cache(slug)
        if success:
            return Response({'message': f'Cache do mangá {slug} invalidado'})
        else:
            return Response({'error': 'Erro ao invalidar cache'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
