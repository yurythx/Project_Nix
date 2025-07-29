"""
Constantes para o app mangas
Define limites e configurações padrão
"""

# Limites de arquivo
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_IMAGE_WIDTH = 4000  # pixels
MAX_IMAGE_HEIGHT = 6000  # pixels

# Tipos de arquivo permitidos
ALLOWED_IMAGE_TYPES = [
    'image/jpeg',
    'image/jpg', 
    'image/png',
    'image/webp',
    'image/gif'
]

ALLOWED_ARCHIVE_TYPES = [
    'application/zip',
    'application/x-zip-compressed',
    'application/x-rar-compressed',
    'application/x-cbz',
    'application/x-cbr'
]

# Limites de conteúdo
MAX_CHAPTER_NUMBER = 9999
MAX_PAGES_PER_CHAPTER = 500
MAX_VOLUMES_PER_MANGA = 200

# Status de mangá
MANGA_STATUS_CHOICES = [
    ('draft', 'Rascunho'),
    ('published', 'Publicado'),
    ('completed', 'Completo'),
    ('on_hold', 'Em Pausa'),
    ('cancelled', 'Cancelado'),
    ('deleted', 'Excluído'),
]

# Status de capítulo
CHAPTER_STATUS_CHOICES = [
    ('draft', 'Rascunho'),
    ('published', 'Publicado'),
    ('scheduled', 'Agendado'),
    ('deleted', 'Excluído'),
]

# Configurações de cache
CACHE_TIMEOUT_SHORT = 60 * 5      # 5 minutos
CACHE_TIMEOUT_MEDIUM = 60 * 15     # 15 minutos  
CACHE_TIMEOUT_LONG = 60 * 60       # 1 hora
CACHE_TIMEOUT_VERY_LONG = 60 * 60 * 24  # 24 horas

# Configurações de paginação
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Configurações de busca
MIN_SEARCH_LENGTH = 2
MAX_SEARCH_LENGTH = 100

# Configurações de rate limiting
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW = 60  # segundos

# Configurações de notificação
MAX_NOTIFICATION_BATCH_SIZE = 1000
NOTIFICATION_RETRY_ATTEMPTS = 3

# Configurações de processamento
MAX_CONCURRENT_UPLOADS = 5
UPLOAD_CHUNK_SIZE = 1024 * 1024  # 1MB

# Configurações de qualidade de imagem
IMAGE_QUALITY_HIGH = 95
IMAGE_QUALITY_MEDIUM = 85
IMAGE_QUALITY_LOW = 70

# Configurações de thumbnail
THUMBNAIL_SIZES = [
    (150, 200),   # Pequeno
    (300, 400),   # Médio
    (600, 800),   # Grande
]

# Configurações de backup
BACKUP_RETENTION_DAYS = 30
MAX_BACKUP_SIZE = 1024 * 1024 * 1024  # 1GB
