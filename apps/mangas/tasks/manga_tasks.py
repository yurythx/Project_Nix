"""
Tasks Celery para processamento assíncrono de mangás
Implementa processamento em background para operações pesadas
"""

import logging
from celery import shared_task
from django.core.cache import cache
from django.db import transaction

from ..factories.service_factory import get_manga_service
from ..models.manga import Manga
from ..models.capitulo import Capitulo

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_manga_upload(self, manga_id: int, file_path: str):
    """
    Processa upload de mangá em background
    
    Args:
        manga_id: ID do mangá
        file_path: Caminho do arquivo a ser processado
        
    Returns:
        dict: Resultado do processamento
    """
    try:
        logger.info(f"Iniciando processamento de upload para manga {manga_id}")
        
        # Aqui seria implementado o processamento do arquivo
        # Por enquanto, apenas simula o processamento
        
        # Atualiza status do mangá
        manga = Manga.objects.get(id=manga_id)
        manga.status = 'processed'
        manga.save()
        
        # Limpa cache relacionado
        cache.delete(f"manga:detail:{manga.slug}")
        
        logger.info(f"Upload processado com sucesso para manga {manga_id}")
        return {
            'status': 'success',
            'manga_id': manga_id,
            'message': 'Upload processado com sucesso'
        }
        
    except Manga.DoesNotExist:
        logger.error(f"Manga {manga_id} não encontrado")
        return {
            'status': 'error',
            'manga_id': manga_id,
            'message': 'Mangá não encontrado'
        }
        
    except Exception as exc:
        logger.error(f"Erro ao processar upload do manga {manga_id}: {exc}")
        
        # Retry com backoff exponencial
        raise self.retry(
            exc=exc,
            countdown=60 * (2 ** self.request.retries),
            max_retries=3
        )


@shared_task
def generate_manga_thumbnails(manga_id: int):
    """
    Gera thumbnails para capas de mangá
    
    Args:
        manga_id: ID do mangá
        
    Returns:
        dict: Resultado da geração
    """
    try:
        logger.info(f"Gerando thumbnails para manga {manga_id}")
        
        manga = Manga.objects.get(id=manga_id)
        
        # Aqui seria implementada a geração de thumbnails
        # Por enquanto, apenas simula o processo
        
        logger.info(f"Thumbnails gerados com sucesso para manga {manga_id}")
        return {
            'status': 'success',
            'manga_id': manga_id,
            'message': 'Thumbnails gerados com sucesso'
        }
        
    except Manga.DoesNotExist:
        logger.error(f"Manga {manga_id} não encontrado")
        return {
            'status': 'error',
            'manga_id': manga_id,
            'message': 'Mangá não encontrado'
        }
        
    except Exception as exc:
        logger.error(f"Erro ao gerar thumbnails para manga {manga_id}: {exc}")
        return {
            'status': 'error',
            'manga_id': manga_id,
            'message': str(exc)
        }


@shared_task
def update_manga_statistics():
    """
    Atualiza estatísticas dos mangás (task periódica)
    
    Returns:
        dict: Resultado da atualização
    """
    try:
        logger.info("Iniciando atualização de estatísticas dos mangás")
        
        updated_count = 0
        
        # Atualiza contagem de capítulos para todos os mangás
        for manga in Manga.objects.filter(is_published=True):
            chapter_count = Capitulo.objects.filter(
                volume__manga=manga,
                is_published=True
            ).count()
            
            if manga.chapter_count != chapter_count:
                manga.chapter_count = chapter_count
                manga.save(update_fields=['chapter_count'])
                updated_count += 1
        
        logger.info(f"Estatísticas atualizadas para {updated_count} mangás")
        return {
            'status': 'success',
            'updated_count': updated_count,
            'message': f'Estatísticas atualizadas para {updated_count} mangás'
        }
        
    except Exception as exc:
        logger.error(f"Erro ao atualizar estatísticas: {exc}")
        return {
            'status': 'error',
            'message': str(exc)
        }


@shared_task
def cleanup_manga_cache():
    """
    Limpa cache expirado de mangás (task periódica)
    
    Returns:
        dict: Resultado da limpeza
    """
    try:
        logger.info("Iniciando limpeza de cache de mangás")
        
        # Lista de chaves de cache para limpar
        cache_keys = []
        
        # Adiciona chaves de mangás
        for manga in Manga.objects.all():
            cache_keys.append(f"manga:detail:{manga.slug}")
            cache_keys.append(f"manga:chapters:{manga.slug}")
        
        # Remove chaves do cache
        cache.delete_many(cache_keys)
        
        logger.info(f"Cache limpo: {len(cache_keys)} chaves removidas")
        return {
            'status': 'success',
            'cleaned_keys': len(cache_keys),
            'message': f'Cache limpo: {len(cache_keys)} chaves removidas'
        }
        
    except Exception as exc:
        logger.error(f"Erro ao limpar cache: {exc}")
        return {
            'status': 'error',
            'message': str(exc)
        }


@shared_task(bind=True, max_retries=3)
def process_chapter_pages(self, chapter_id: int):
    """
    Processa páginas de um capítulo em background
    
    Args:
        chapter_id: ID do capítulo
        
    Returns:
        dict: Resultado do processamento
    """
    try:
        logger.info(f"Processando páginas do capítulo {chapter_id}")
        
        chapter = Capitulo.objects.get(id=chapter_id)
        
        # Aqui seria implementado o processamento das páginas
        # Por enquanto, apenas simula o processo
        
        # Atualiza status do capítulo
        chapter.status = 'processed'
        chapter.save()
        
        logger.info(f"Páginas processadas com sucesso para capítulo {chapter_id}")
        return {
            'status': 'success',
            'chapter_id': chapter_id,
            'message': 'Páginas processadas com sucesso'
        }
        
    except Capitulo.DoesNotExist:
        logger.error(f"Capítulo {chapter_id} não encontrado")
        return {
            'status': 'error',
            'chapter_id': chapter_id,
            'message': 'Capítulo não encontrado'
        }
        
    except Exception as exc:
        logger.error(f"Erro ao processar páginas do capítulo {chapter_id}: {exc}")
        
        # Retry com backoff exponencial
        raise self.retry(
            exc=exc,
            countdown=30 * (2 ** self.request.retries),
            max_retries=3
        )
