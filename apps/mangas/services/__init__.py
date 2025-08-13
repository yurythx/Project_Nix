# Pacote de serviços do app mangas
# Imports existentes (manter todos)
from .unified_manga_service import unified_manga_service, UnifiedMangaService
from .reading_progress_service import reading_progress_service, ReadingProgressService

# Adicionar aos exports
__all__ = [
    'unified_manga_service',
    'UnifiedMangaService',
    'reading_progress_service',
    'ReadingProgressService'
]