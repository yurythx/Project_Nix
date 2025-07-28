"""
Módulo para exceções personalizadas do app mangas.
"""
from django.utils.translation import gettext_lazy as _

class MangaException(Exception):
    """Classe base para exceções do app mangas."""
    default_message = _("Ocorreu um erro no processamento do mangá.")
    
    def __init__(self, message=None, **kwargs):
        self.message = message or self.default_message
        self.extra_data = kwargs
        super().__init__(self.message)

class MangaValidationError(MangaException):
    """Exceção lançada quando há erros de validação em um mangá."""
    default_message = _("Erro de validação do mangá.")

class MangaNotFoundError(MangaException):
    """Exceção lançada quando um mangá não é encontrado."""
    default_message = _("Mangá não encontrado.")

class ChapterNotFoundError(MangaException):
    """Exceção lançada quando um capítulo não é encontrado."""
    default_message = _("Capítulo não encontrado.")

class PageNotFoundError(MangaException):
    """Exceção lançada quando uma página não é encontrada."""
    default_message = _("Página não encontrada.")

class DuplicateMangaError(MangaException):
    """Exceção lançada quando tenta-se criar um mangá duplicado."""
    default_message = _("Já existe um mangá com este título.")

class DuplicateChapterError(MangaException):
    """Exceção lançada quando tenta-se criar um capítulo duplicado."""
    default_message = _("Já existe um capítulo com este número.")

class DuplicatePageError(MangaException):
    """Exceção lançada quando tenta-se criar uma página duplicada."""
    default_message = _("Já existe uma página com este número.")

class InvalidFileError(MangaException):
    """Exceção lançada quando um arquivo inválido é fornecido."""
    default_message = _("Arquivo inválido ou corrompido.")

class FileTooLargeError(MangaException):
    """Exceção lançada quando um arquivo excede o tamanho máximo permitido."""
    default_message = _("O arquivo é muito grande.")

class UnsupportedFileTypeError(MangaException):
    """Exceção lançada quando um tipo de arquivo não suportado é fornecido."""
    default_message = _("Tipo de arquivo não suportado.")

class MangaPublishingError(MangaException):
    """Exceção lançada quando ocorre um erro ao publicar um mangá."""
    default_message = _("Erro ao publicar o mangá.")

class ChapterPublishingError(MangaException):
    """Exceção lançada quando ocorre um erro ao publicar um capítulo."""
    default_message = _("Erro ao publicar o capítulo.")

class PageProcessingError(MangaException):
    """Exceção lançada quando ocorre um erro ao processar uma página."""
    default_message = _("Erro ao processar a página.")
