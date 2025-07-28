"""
Este arquivo é mantido para compatibilidade com versões antigas do Django.
Todos os modelos foram movidos para o pacote models/.
"""

# Importa todos os modelos do pacote models
from .models import *  # noqa

# Esta linha garante que o Django ainda reconheça os modelos
# quando importados diretamente de 'mangas.models'
__all__ = [
    'Manga',
    'Volume',
    'Capitulo',
    'Pagina'
]
