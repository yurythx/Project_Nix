"""Constants module for Manga app."""

# Image settings
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_IMAGE_WIDTH = 4096  # 4K width
MAX_IMAGE_HEIGHT = 4096  # 4K height
ALLOWED_IMAGE_TYPES = [
    'image/jpeg', 'image/jpg', 'image/png', 'image/webp', 
    'image/gif', 'image/bmp', 'image/tiff', 'image/tif'
]
ALLOWED_IMAGE_EXTENSIONS = [
    '.jpg', '.jpeg',  # JPEG images
    '.png',           # Portable Network Graphics
    '.webp',          # WebP format
    '.gif',           # Graphics Interchange Format
    '.bmp',           # Bitmap Image File
    '.tiff', '.tif',  # Tagged Image File Format
    '.heic', '.heif', # High Efficiency Image Format
    '.avif'           # AV1 Image File Format
]

# Archive settings
MAX_ARCHIVE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_ARCHIVE_EXTENSIONS = [
    '.zip',         # ZIP archive
    '.rar',         # Roshal Archive
    '.7z',          # 7-Zip archive
    '.tar',         # TAR archive
    '.tar.gz',      # TAR GZIP archive
    '.tar.bz2',     # TAR BZIP2 archive
    '.tar.xz',      # TAR XZ archive
    '.cbz',         # Comic Book ZIP archive
    '.cbr',         # Comic Book RAR archive
    '.cb7',         # Comic Book 7Z archive
    '.cbt',         # Comic Book TAR archive
    '.cba',         # Comic Book ACE archive (menos comum)
    '.pdf'          # Portable Document Format
]

# Chapter settings
MAX_CHAPTER_NUMBER = 9999
MAX_PAGES_PER_CHAPTER = 200

# Pagination
ITEMS_PER_PAGE = 20

# Messages
MESSAGES = {
    'archive_too_large': 'O arquivo é muito grande. Tamanho máximo permitido: {}MB',
    'invalid_archive': 'Tipo de arquivo não suportado. Use: {}',
    'no_images_found': 'Nenhuma imagem válida encontrada no arquivo',
    'invalid_image': 'Tipo de imagem não suportado. Use: {}',
}
