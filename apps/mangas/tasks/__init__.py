"""
Tasks Celery para processamento assíncrono de mangás
"""

from .manga_tasks import (
    process_manga_upload,
    generate_manga_thumbnails,
    update_manga_statistics,
    cleanup_manga_cache,
    process_chapter_pages
)

__all__ = [
    'process_manga_upload',
    'generate_manga_thumbnails', 
    'update_manga_statistics',
    'cleanup_manga_cache',
    'process_chapter_pages'
]
