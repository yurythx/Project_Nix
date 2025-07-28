"""
Módulo de modelos do app mangas.
"""

from .manga import Manga
from .volume import Volume
from .capitulo import Capitulo
from .pagina import Pagina

# Tornar os modelos disponíveis diretamente do pacote
__all__ = [
    'Manga',
    'Volume',
    'Capitulo',
    'Pagina',
]