# 🛠️ Recomendações de Implementação - App Mangas

## 🎯 **IMPLEMENTAÇÕES PRIORITÁRIAS**

### **1. Repository Pattern Completo**

#### **Criar IMangaRepository:**
```python
# apps/mangas/interfaces/repositories.py
from abc import ABC, abstractmethod
from typing import Optional, List
from django.db.models import QuerySet

class IMangaRepository(ABC):
    @abstractmethod
    def get_by_slug(self, slug: str) -> Optional[Manga]:
        pass
    
    @abstractmethod
    def get_published_mangas(self) -> QuerySet[Manga]:
        pass
    
    @abstractmethod
    def get_manga_with_chapters(self, slug: str) -> Optional[Manga]:
        pass
```

#### **Implementar DjangoMangaRepository:**
```python
# apps/mangas/repositories/manga_repository.py
class DjangoMangaRepository(IMangaRepository):
    def get_by_slug(self, slug: str) -> Optional[Manga]:
        try:
            return Manga.objects.select_related('created_by').get(
                slug=slug, 
                is_published=True
            )
        except Manga.DoesNotExist:
            return None
    
    def get_published_mangas(self) -> QuerySet[Manga]:
        return Manga.objects.filter(
            is_published=True,
            status='published'
        ).select_related('created_by').prefetch_related('volumes')
    
    def get_manga_with_chapters(self, slug: str) -> Optional[Manga]:
        try:
            return Manga.objects.select_related('created_by').prefetch_related(
                'volumes__capitulos__paginas'
            ).get(slug=slug)
        except Manga.DoesNotExist:
            return None
```

### **2. Service Layer Funcional**

#### **MangaService Simplificado:**
```python
# apps/mangas/services/manga_service.py
class MangaService(IMangaService):
    def __init__(self, repository: IMangaRepository):
        self.repository = repository
        self.logger = logging.getLogger(__name__)
    
    def get_manga_by_slug(self, slug: str) -> Manga:
        manga = self.repository.get_by_slug(slug)
        if not manga:
            raise MangaNotFoundError(f"Mangá '{slug}' não encontrado")
        return manga
    
    def get_manga_context(self, manga: Manga) -> Dict[str, Any]:
        """Retorna contexto completo para templates"""
        return {
            'volumes': manga.volumes.prefetch_related('capitulos').all(),
            'total_chapters': manga.get_total_chapters(),
            'latest_chapter': manga.get_latest_chapter(),
            'reading_progress': self._get_reading_progress(manga),
        }
    
    def _get_reading_progress(self, manga: Manga) -> Dict[str, Any]:
        # Lógica de progresso de leitura
        pass
```

### **3. Views Refatoradas**

#### **MangaDetailView Simplificada:**
```python
# apps/mangas/views/manga_views.py
class MangaDetailView(DetailView):
    model = Manga
    template_name = 'mangas/manga_detail.html'
    context_object_name = 'manga'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manga_service = service_factory.create_manga_service()
    
    def get_object(self, queryset=None):
        return self.manga_service.get_manga_by_slug(self.kwargs['slug'])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.manga_service.get_manga_context(self.object))
        return context
```

### **4. Cache Strategy**

#### **Cache em Múltiplas Camadas:**
```python
# apps/mangas/services/cache_service.py
from django.core.cache import cache
from django.conf import settings

class MangaCacheService:
    CACHE_TIMEOUT = 60 * 15  # 15 minutos
    
    @staticmethod
    def get_manga_cache_key(slug: str) -> str:
        return f"manga:detail:{slug}"
    
    @staticmethod
    def get_chapter_cache_key(manga_slug: str, chapter_slug: str) -> str:
        return f"manga:chapter:{manga_slug}:{chapter_slug}"
    
    def cache_manga(self, manga: Manga) -> None:
        cache_key = self.get_manga_cache_key(manga.slug)
        cache.set(cache_key, manga, self.CACHE_TIMEOUT)
    
    def get_cached_manga(self, slug: str) -> Optional[Manga]:
        cache_key = self.get_manga_cache_key(slug)
        return cache.get(cache_key)
```

### **5. Processamento Assíncrono**

#### **Tasks Celery:**
```python
# apps/mangas/tasks.py
from celery import shared_task
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def process_manga_upload(self, manga_id: int, file_path: str):
    """Processa upload de mangá em background"""
    try:
        service = MangaFileProcessorService()
        service.process_uploaded_file(manga_id, file_path)
        logger.info(f"Manga {manga_id} processado com sucesso")
    except Exception as exc:
        logger.error(f"Erro ao processar manga {manga_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)

@shared_task
def generate_manga_thumbnails(manga_id: int):
    """Gera thumbnails para capas de mangá"""
    try:
        service = MangaThumbnailService()
        service.generate_thumbnails(manga_id)
    except Exception as exc:
        logger.error(f"Erro ao gerar thumbnails para manga {manga_id}: {exc}")
```

### **6. Testes Abrangentes**

#### **Testes de Service:**
```python
# apps/mangas/tests/test_services.py
import pytest
from unittest.mock import Mock, patch
from apps.mangas.services.manga_service import MangaService
from apps.mangas.exceptions import MangaNotFoundError

class TestMangaService:
    def setup_method(self):
        self.mock_repository = Mock()
        self.service = MangaService(self.mock_repository)
    
    def test_get_manga_by_slug_success(self):
        # Arrange
        manga = Mock()
        manga.slug = 'test-manga'
        self.mock_repository.get_by_slug.return_value = manga
        
        # Act
        result = self.service.get_manga_by_slug('test-manga')
        
        # Assert
        assert result == manga
        self.mock_repository.get_by_slug.assert_called_once_with('test-manga')
    
    def test_get_manga_by_slug_not_found(self):
        # Arrange
        self.mock_repository.get_by_slug.return_value = None
        
        # Act & Assert
        with pytest.raises(MangaNotFoundError):
            self.service.get_manga_by_slug('nonexistent')
```

### **7. Logging Estruturado**

#### **Configuração de Logging:**
```python
# apps/mangas/services/manga_service.py
import structlog

logger = structlog.get_logger(__name__)

class MangaService:
    def create_manga(self, manga_data: Dict[str, Any], user: User) -> Manga:
        logger.info(
            "Creating manga",
            manga_title=manga_data.get('title'),
            user_id=user.id,
            user_email=user.email
        )
        
        try:
            manga = self.repository.create(manga_data, user)
            logger.info(
                "Manga created successfully",
                manga_id=manga.id,
                manga_slug=manga.slug
            )
            return manga
        except Exception as e:
            logger.error(
                "Failed to create manga",
                error=str(e),
                manga_title=manga_data.get('title'),
                user_id=user.id
            )
            raise
```

### **8. API REST Completa**

#### **Serializers DRF:**
```python
# apps/mangas/serializers.py
from rest_framework import serializers
from .models import Manga, Capitulo, Pagina

class MangaListSerializer(serializers.ModelSerializer):
    total_chapters = serializers.IntegerField(read_only=True)
    latest_chapter = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Manga
        fields = ['id', 'title', 'slug', 'cover_image', 'author', 
                 'total_chapters', 'latest_chapter', 'created_at']

class MangaDetailSerializer(serializers.ModelSerializer):
    volumes = serializers.StringRelatedField(many=True, read_only=True)
    
    class Meta:
        model = Manga
        fields = '__all__'
```

#### **ViewSets API:**
```python
# apps/mangas/api/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

class MangaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Manga.objects.filter(is_published=True)
    serializer_class = MangaListSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['author', 'status']
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return MangaDetailSerializer
        return MangaListSerializer
    
    @action(detail=True, methods=['get'])
    def chapters(self, request, slug=None):
        manga = self.get_object()
        chapters = manga.get_published_chapters()
        serializer = ChapterSerializer(chapters, many=True)
        return Response(serializer.data)
```

## 📊 **MÉTRICAS DE SUCESSO**

### **KPIs Técnicos:**
- **Cobertura de Testes:** 80%+ 
- **Tempo de Resposta:** <200ms para listagem
- **Cache Hit Rate:** 90%+
- **Uptime:** 99.9%

### **KPIs de Negócio:**
- **Tempo de Upload:** <30s para arquivos ZIP
- **Taxa de Erro:** <1%
- **Satisfação do Usuário:** 4.5/5
- **Performance Mobile:** 90+ no Lighthouse

---

**Implementando essas recomendações, o app mangas se tornará um sistema robusto, escalável e maintível, seguindo as melhores práticas de desenvolvimento Django.** 🚀📚✨
