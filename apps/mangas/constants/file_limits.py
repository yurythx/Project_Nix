from django.conf import settings

# Limites de tamanho de arquivo
MAX_UPLOAD_SIZE_MB = getattr(settings, 'MAX_UPLOAD_SIZE_MB', 100)
MAX_UPLOAD_SIZE = MAX_UPLOAD_SIZE_MB * 1024 * 1024  # 100 MB em bytes

# Limites de sessão de upload
MAX_SESSION_SIZE_MB = getattr(settings, 'MAX_SESSION_SIZE_MB', 500)
MAX_FILES_PER_SESSION = getattr(settings, 'MAX_FILES_PER_SESSION', 100)

# Dimensões de imagem
MIN_IMAGE_WIDTH = getattr(settings, 'MIN_IMAGE_WIDTH', 300)
MIN_IMAGE_HEIGHT = getattr(settings, 'MIN_IMAGE_HEIGHT', 450)
MAX_IMAGE_WIDTH = getattr(settings, 'MAX_IMAGE_WIDTH', 2500)
MAX_IMAGE_HEIGHT = getattr(settings, 'MAX_IMAGE_HEIGHT', 3500)

# Extensões e tipos MIME permitidos
ALLOWED_IMAGE_EXTENSIONS = getattr(settings, 'ALLOWED_IMAGE_EXTENSIONS', ['jpg', 'jpeg', 'png', 'gif', 'webp'])
ALLOWED_IMAGE_MIME_TYPES = getattr(settings, 'ALLOWED_IMAGE_MIME_TYPES', [
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp'
])

ALLOWED_ARCHIVE_EXTENSIONS = getattr(settings, 'ALLOWED_ARCHIVE_EXTENSIONS', ['zip', 'rar', 'cbz', 'cbr', 'pdf'])
ALLOWED_ARCHIVE_MIME_TYPES = getattr(settings, 'ALLOWED_ARCHIVE_MIME_TYPES', [
    'application/zip',
    'application/x-rar-compressed',
    'application/vnd.comicbook+zip',
    'application/vnd.comicbook+rar',
    'application/pdf'
])

# Limites de capítulos e páginas
MAX_CHAPTERS_PER_VOLUME = getattr(settings, 'MAX_CHAPTERS_PER_VOLUME', 200)
MAX_PAGES_PER_CHAPTER = getattr(settings, 'MAX_PAGES_PER_CHAPTER', 500)

# Paginação
DEFAULT_PAGE_SIZE = getattr(settings, 'DEFAULT_PAGE_SIZE', 20)

# Mensagens de erro padronizadas
ERROR_MESSAGES = {
    'invalid_file_type': 'Tipo de arquivo não permitido. Extensões permitidas: {}.',
    'file_too_large': 'O arquivo é muito grande. O tamanho máximo permitido é {} MB.',
    'image_dimensions_too_small': 'A imagem é muito pequena. As dimensões mínimas são {}x{} pixels.',
    'image_dimensions_too_large': 'A imagem é muito grande. As dimensões máximas são {}x{} pixels.',
    'invalid_archive_content': 'O arquivo compactado contém conteúdo inválido ou não suportado.',
    'number_not_unique': 'Este número já existe para este {}.',
    'title_not_unique': 'Este título já existe para este {}.'
}

# Chaves de cache
CACHE_KEYS = {
    'manga_detail': 'manga_detail_{slug}',
    'manga_list': 'manga_list_page_{page}',
    'volume_detail': 'volume_detail_{slug}',
    'chapter_detail': 'chapter_detail_{slug}',
    'manga_stats': 'manga_stats',
    'latest_updates': 'latest_manga_updates'
}

# Configurações de processamento de imagem/arquivo
THUMBNAIL_SIZE = getattr(settings, 'THUMBNAIL_SIZE', (150, 225))
PREVIEW_SIZE = getattr(settings, 'PREVIEW_SIZE', (800, 1200))
COMPRESSION_QUALITY = getattr(settings, 'COMPRESSION_QUALITY', 85)

def get_allowed_image_extensions_str():
    return ', '.join(ALLOWED_IMAGE_EXTENSIONS)

def get_allowed_archive_extensions_str():
    return ', '.join(ALLOWED_ARCHIVE_EXTENSIONS)

def get_max_upload_size_mb():
    return MAX_UPLOAD_SIZE_MB

def get_min_image_dimensions_str():
    return f"{MIN_IMAGE_WIDTH}x{MIN_IMAGE_HEIGHT}"

def get_max_image_dimensions_str():
    return f"{MAX_IMAGE_WIDTH}x{MAX_IMAGE_HEIGHT}"