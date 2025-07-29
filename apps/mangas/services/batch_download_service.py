"""
Serviço para gerenciar downloads em lote de capítulos.
"""

import logging
import os
import zipfile
import tempfile
from typing import List, Dict, Any, Optional
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from PIL import Image
import io

from ..models.batch_download import BatchDownload, BatchDownloadItem, BatchDownloadTemplate
from ..models.capitulo import Capitulo
from ..models.notifications import Notification
from .download_service import DownloadService

logger = logging.getLogger(__name__)
User = get_user_model()

class BatchDownloadService:
    """
    Serviço para gerenciar downloads em lote de capítulos.
    """
    
    def __init__(self):
        self.download_service = DownloadService()
        self.max_concurrent_downloads = 3
        self.batch_timeout = 3600  # 1 hora
    
    def create_batch_download(self, user: User, manga_id: int, name: str, 
                             start_chapter: Optional[int] = None, end_chapter: Optional[int] = None,
                             volume_filter: Optional[str] = None, quality: str = 'original',
                             template_id: Optional[int] = None) -> BatchDownload:
        """
        Cria um novo download em lote.
        """
        from ..models.manga import Manga
        
        try:
            manga = Manga.objects.get(id=manga_id)
        except Manga.DoesNotExist:
            raise ValueError("Mangá não encontrado.")
        
        # Aplicar template se especificado
        if template_id:
            template = BatchDownloadTemplate.objects.get(id=template_id, user=user)
            quality = template.quality
            max_concurrent = template.max_concurrent_downloads
            retry_failed = template.retry_failed
            max_retries = template.max_retries
            if not volume_filter:
                volume_filter = template.default_volume_filter
        else:
            max_concurrent = 3
            retry_failed = True
            max_retries = 3
        
        # Criar download em lote
        batch_download = BatchDownload.objects.create(
            user=user,
            name=name,
            manga=manga,
            start_chapter=start_chapter,
            end_chapter=end_chapter,
            volume_filter=volume_filter,
            quality=quality,
            max_concurrent_downloads=max_concurrent,
            retry_failed=retry_failed,
            max_retries=max_retries
        )
        
        # Preparar capítulos para download
        chapters = batch_download.get_chapters_to_download()
        batch_download.total_chapters = len(chapters)
        batch_download.save()
        
        # Criar itens de download
        self._create_batch_items(batch_download, chapters)
        
        # Iniciar processamento em background
        self._start_batch_processing(batch_download)
        
        logger.info(f"Download em lote criado: {batch_download.id} para {user.username}")
        return batch_download
    
    def get_user_batch_downloads(self, user: User, status: Optional[str] = None) -> List[BatchDownload]:
        """
        Obtém downloads em lote de um usuário.
        """
        queryset = BatchDownload.objects.filter(user=user).select_related('manga').order_by('-created_at')
        
        if status:
            queryset = queryset.filter(status=status)
        
        return list(queryset)
    
    def get_batch_download_status(self, batch_id: int, user: User) -> Dict[str, Any]:
        """
        Obtém status detalhado de um download em lote.
        """
        try:
            batch = BatchDownload.objects.get(id=batch_id, user=user)
        except BatchDownload.DoesNotExist:
            raise ValueError("Download em lote não encontrado.")
        
        items = BatchDownloadItem.objects.filter(batch_download=batch)
        
        return {
            'id': batch.id,
            'name': batch.name,
            'status': batch.status,
            'progress_percentage': batch.progress_percentage,
            'total_chapters': batch.total_chapters,
            'completed_chapters': batch.completed_chapters,
            'failed_chapters': batch.failed_chapters,
            'total_size_mb': batch.total_size_mb,
            'downloaded_size_mb': batch.downloaded_size_mb,
            'file_url': batch.get_file_url(),
            'created_at': batch.created_at,
            'started_at': batch.started_at,
            'completed_at': batch.completed_at,
            'expires_at': batch.expires_at,
            'items_by_status': {
                'pending': items.filter(status='pending').count(),
                'downloading': items.filter(status='downloading').count(),
                'completed': items.filter(status='completed').count(),
                'failed': items.filter(status='failed').count(),
            }
        }
    
    def cancel_batch_download(self, batch_id: int, user: User) -> bool:
        """
        Cancela um download em lote.
        """
        try:
            batch = BatchDownload.objects.get(id=batch_id, user=user)
        except BatchDownload.DoesNotExist:
            raise ValueError("Download em lote não encontrado.")
        
        if batch.status not in ['pending', 'processing']:
            raise ValueError("Download em lote não pode ser cancelado.")
        
        batch.cancel()
        
        # Cancelar itens pendentes
        BatchDownloadItem.objects.filter(
            batch_download=batch,
            status__in=['pending', 'downloading']
        ).update(status='cancelled')
        
        logger.info(f"Download em lote cancelado: {batch_id} por {user.username}")
        return True
    
    def pause_batch_download(self, batch_id: int, user: User) -> bool:
        """
        Pausa um download em lote.
        """
        try:
            batch = BatchDownload.objects.get(id=batch_id, user=user)
        except BatchDownload.DoesNotExist:
            raise ValueError("Download em lote não encontrado.")
        
        if batch.status != 'processing':
            raise ValueError("Download em lote não pode ser pausado.")
        
        batch.pause()
        
        logger.info(f"Download em lote pausado: {batch_id} por {user.username}")
        return True
    
    def resume_batch_download(self, batch_id: int, user: User) -> bool:
        """
        Retoma um download em lote.
        """
        try:
            batch = BatchDownload.objects.get(id=batch_id, user=user)
        except BatchDownload.DoesNotExist:
            raise ValueError("Download em lote não encontrado.")
        
        if batch.status != 'paused':
            raise ValueError("Download em lote não pode ser retomado.")
        
        batch.resume()
        
        # Retomar processamento
        self._start_batch_processing(batch)
        
        logger.info(f"Download em lote retomado: {batch_id} por {user.username}")
        return True
    
    def delete_batch_download(self, batch_id: int, user: User) -> bool:
        """
        Remove um download em lote.
        """
        try:
            batch = BatchDownload.objects.get(id=batch_id, user=user)
        except BatchDownload.DoesNotExist:
            raise ValueError("Download em lote não encontrado.")
        
        # Remover arquivo se existir
        if batch.file_path and default_storage.exists(batch.file_path):
            default_storage.delete(batch.file_path)
        
        batch.delete()
        
        logger.info(f"Download em lote removido: {batch_id} por {user.username}")
        return True
    
    def get_batch_download_stats(self, user: User) -> Dict[str, Any]:
        """
        Obtém estatísticas de downloads em lote do usuário.
        """
        batches = BatchDownload.objects.filter(user=user)
        
        stats = {
            'total_batches': batches.count(),
            'completed_batches': batches.filter(status='completed').count(),
            'pending_batches': batches.filter(status='pending').count(),
            'processing_batches': batches.filter(status='processing').count(),
            'failed_batches': batches.filter(status='failed').count(),
            'total_chapters_downloaded': sum(batch.completed_chapters for batch in batches),
            'total_size_downloaded_mb': sum(batch.downloaded_size_mb for batch in batches),
        }
        
        return stats
    
    def create_batch_template(self, user: User, name: str, quality: str = 'original',
                             max_concurrent_downloads: int = 3, retry_failed: bool = True,
                             max_retries: int = 3, default_volume_filter: str = '',
                             include_unpublished: bool = False) -> BatchDownloadTemplate:
        """
        Cria um template de download em lote.
        """
        template = BatchDownloadTemplate.objects.create(
            user=user,
            name=name,
            quality=quality,
            max_concurrent_downloads=max_concurrent_downloads,
            retry_failed=retry_failed,
            max_retries=max_retries,
            default_volume_filter=default_volume_filter,
            include_unpublished=include_unpublished
        )
        
        logger.info(f"Template de download criado: {template.id} por {user.username}")
        return template
    
    def get_user_templates(self, user: User) -> List[BatchDownloadTemplate]:
        """
        Obtém templates de download do usuário.
        """
        return list(BatchDownloadTemplate.objects.filter(
            user=user
        ).order_by('name'))
    
    def get_public_templates(self) -> List[BatchDownloadTemplate]:
        """
        Obtém templates públicos.
        """
        return list(BatchDownloadTemplate.objects.filter(
            is_public=True
        ).order_by('name'))
    
    def _create_batch_items(self, batch_download: BatchDownload, chapters: List[Capitulo]):
        """
        Cria itens de download para o lote.
        """
        items = []
        for i, chapter in enumerate(chapters):
            item = BatchDownloadItem(
                batch_download=batch_download,
                capitulo=chapter,
                priority=i
            )
            items.append(item)
        
        BatchDownloadItem.objects.bulk_create(items)
    
    def _start_batch_processing(self, batch_download: BatchDownload):
        """
        Inicia processamento do lote em background.
        """
        batch_download.start_processing()
        
        # Em produção, use Celery ou similar
        # Aqui simulamos o processamento
        self._process_batch_async(batch_download)
    
    def _process_batch_async(self, batch_download: BatchDownload):
        """
        Processa o lote de forma assíncrona.
        """
        try:
            # Obter itens pendentes
            pending_items = BatchDownloadItem.objects.filter(
                batch_download=batch_download,
                status='pending'
            ).order_by('priority')
            
            if not pending_items:
                self._finalize_batch(batch_download)
                return
            
            # Processar itens em paralelo (simulado)
            for item in pending_items[:batch_download.max_concurrent_downloads]:
                self._process_batch_item(item)
            
            # Verificar se todos foram processados
            remaining_pending = BatchDownloadItem.objects.filter(
                batch_download=batch_download,
                status='pending'
            ).count()
            
            if remaining_pending == 0:
                self._finalize_batch(batch_download)
            else:
                # Continuar processamento
                self._process_batch_async(batch_download)
                
        except Exception as e:
            logger.error(f"Erro no processamento do lote {batch_download.id}: {str(e)}")
            batch_download.mark_as_failed(str(e))
    
    def _process_batch_item(self, item: BatchDownloadItem):
        """
        Processa um item individual do lote.
        """
        try:
            item.status = 'downloading'
            item.save()
            
            # Usar serviço de download individual
            download = self.download_service.create_download(item.batch_download.user, item.capitulo)
            
            # Aguardar conclusão (em produção, seria assíncrono)
            if download.status == 'completed':
                item.mark_as_completed(download.file_path, download.file_size)
                self._update_batch_progress(item.batch_download)
            else:
                item.mark_as_failed(download.error_message)
                
        except Exception as e:
            logger.error(f"Erro ao processar item {item.id}: {str(e)}")
            item.mark_as_failed(str(e))
    
    def _finalize_batch(self, batch_download: BatchDownload):
        """
        Finaliza o lote criando o arquivo ZIP.
        """
        try:
            # Verificar se há itens concluídos
            completed_items = BatchDownloadItem.objects.filter(
                batch_download=batch_download,
                status='completed'
            )
            
            if not completed_items:
                batch_download.mark_as_failed("Nenhum capítulo foi baixado com sucesso")
                return
            
            # Criar arquivo ZIP com todos os capítulos
            file_path, file_size = self._create_batch_zip(batch_download, completed_items)
            
            # Marcar como concluído
            batch_download.mark_as_completed(file_path, file_size)
            
            # Enviar notificação
            self._send_batch_completion_notification(batch_download)
            
            logger.info(f"Download em lote concluído: {batch_download.id}")
            
        except Exception as e:
            logger.error(f"Erro ao finalizar lote {batch_download.id}: {str(e)}")
            batch_download.mark_as_failed(str(e))
    
    def _create_batch_zip(self, batch_download: BatchDownload, 
                         completed_items: List[BatchDownloadItem]) -> tuple:
        """
        Cria arquivo ZIP com todos os capítulos do lote.
        """
        # Criar arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            with zipfile.ZipFile(temp_file, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Adicionar cada capítulo ao ZIP
                for item in completed_items:
                    if item.file_path and default_storage.exists(item.file_path):
                        # Ler arquivo do capítulo
                        with default_storage.open(item.file_path, 'rb') as chapter_file:
                            # Nome do arquivo no ZIP
                            filename = f"capitulo_{item.capitulo.number:03d}.zip"
                            zip_file.writestr(filename, chapter_file.read())
                
                # Adicionar arquivo de informações
                info_content = self._create_batch_info_file(batch_download, completed_items)
                zip_file.writestr('info.txt', info_content)
            
            # Mover para storage
            file_path = f"batch_downloads/{batch_download.user.id}/{batch_download.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.zip"
            
            with open(temp_file.name, 'rb') as f:
                default_storage.save(file_path, ContentFile(f.read()))
            
            # Obter tamanho do arquivo
            file_size = default_storage.size(file_path)
            
            # Limpar arquivo temporário
            os.unlink(temp_file.name)
            
            return file_path, file_size
    
    def _create_batch_info_file(self, batch_download: BatchDownload, 
                               completed_items: List[BatchDownloadItem]) -> str:
        """
        Cria arquivo de informações do lote.
        """
        info = f"""Informações do Download em Lote

Nome: {batch_download.name}
Mangá: {batch_download.manga.title}
Capítulos: {batch_download.completed_chapters}/{batch_download.total_chapters}
Qualidade: {batch_download.get_quality_display()}
Tamanho Total: {batch_download.downloaded_size_mb:.1f} MB

Capítulos Incluídos:
"""
        
        for item in completed_items:
            info += f"- Capítulo {item.capitulo.number}"
            if item.capitulo.title:
                info += f": {item.capitulo.title}"
            info += f" ({item.file_size / (1024*1024):.1f} MB)\n"
        
        info += f"""
Criado em: {batch_download.created_at.strftime('%d/%m/%Y %H:%M:%S')}
Concluído em: {batch_download.completed_at.strftime('%d/%m/%Y %H:%M:%S')}

---
Project Nix - Sistema de Leitura de Mangá
"""
        return info
    
    def _update_batch_progress(self, batch_download: BatchDownload):
        """
        Atualiza o progresso do lote.
        """
        items = BatchDownloadItem.objects.filter(batch_download=batch_download)
        
        batch_download.completed_chapters = items.filter(status='completed').count()
        batch_download.failed_chapters = items.filter(status='failed').count()
        batch_download.downloaded_size_mb = sum(
            item.file_size / (1024*1024) for item in items.filter(status='completed') if item.file_size
        )
        
        batch_download.save()
    
    def _send_batch_completion_notification(self, batch_download: BatchDownload):
        """
        Envia notificação de conclusão do lote.
        """
        title = f"Download em lote concluído!"
        message = f"O lote '{batch_download.name}' foi concluído com sucesso"
        
        data = {
            'batch_id': batch_download.id,
            'manga_id': batch_download.manga.id,
            'manga_title': batch_download.manga.title,
            'completed_chapters': batch_download.completed_chapters,
            'total_chapters': batch_download.total_chapters,
        }
        
        Notification.objects.create(
            recipient=batch_download.user,
            notification_type='download_complete',
            title=title,
            message=message,
            data=data
        ) 