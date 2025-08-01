from .manga_form import MangaForm, CapituloForm, CapituloCompleteForm, PaginaForm
from .unified_forms import (
    UnifiedMangaForm,
    UnifiedVolumeForm,
    UnifiedCapituloForm,
    UnifiedCapituloCompleteForm,
    UnifiedPaginaForm,
    # UnifiedBulkUploadForm,  # Comentado temporariamente
)

__all__ = [
    # Formulários originais
    'MangaForm',
    'CapituloForm', 
    'CapituloCompleteForm',
    'PaginaForm',
    
    # Formulários unificados
    'UnifiedMangaForm',
    'UnifiedVolumeForm',
    'UnifiedCapituloForm',
    'UnifiedCapituloCompleteForm',
    'UnifiedPaginaForm',
    # 'UnifiedBulkUploadForm',  # Comentado temporariamente
]