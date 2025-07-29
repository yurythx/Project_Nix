"""
Serviço para gerenciar downloads offline de capítulos de mangá.
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
from django.core.cache import cache
from django.db import transaction
from PIL import Image
import io

from ..models.offline_download import OfflineDownload, DownloadQueue, DownloadPreferences
from ..models.capitulo import Capitulo
from ..models.pagina import Pagina

logger = logging.getLogger(__name__)
User = get_user_model()

class DownloadService:
    """
    Serviço para gerenciar downloads offline de capítulos.
    """
    
    def __init__(self):
        self.max_concurrent_downloads = 3
        self.download_timeout = 300  # 5 minutos
        self.cache_timeout = 600  # 10 minutos
    
    def create_download(self, user: User, capitulo: Capitulo) -> OfflineDownload:
        """
        Cria um novo download para um capítulo.
        """
        # Verificar se já existe um download ativo
        existing_download = OfflineDownload.objects.filter(
            user=user,
            capitulo=capitulo
        ).first()
        
        if existing_download:
            if existing_download.status == 'completed' and existing_download.is_available:
                return existing_download
            elif existing_download.status in ['pending', 'downloading']:
                raise ValueError("Download já está em andamento.")
            else:
                # Limpar download anterior
                existing_download.cleanup_file()
        
        # Verificar preferências do usuário
        preferences = self._get_user_preferences(user)
        
        # Estimar tamanho do download
        estimated_size = self._estimate_download_size(capitulo, preferences.download_quality)
        
        # Verificar se há espaço suficiente
        if not preferences.can_download(estimated_size):
            raise ValueError("Espaço insuficiente para o download.")
        
        # Criar download
        download = OfflineDownload.objects.create(
            user=user,
            capitulo=capitulo,
            status='pending'
        )
        
        # Iniciar download em background
        self._start_download_async(download)
        
        logger.info(f"Download criado: {download.id} para {user.username}")
        return download
    
    def get_user_downloads(self, user: User, status: Optional[str] = None) -> List[OfflineDownload]:
        """
        Obtém downloads de um usuário.
        """
        queryset = OfflineDownload.objects.filter(user=user).select_related(
            'capitulo__manga', 'capitulo__volume'
        ).order_by('-created_at')
        
        if status:
            queryset = queryset.filter(status=status)
        
        return list(queryset)
    
    def get_download_status(self, download_id: int, user: User) -> Dict[str, Any]:
        """
        Obtém status detalhado de um download.
        """
        try:
            download = OfflineDownload.objects.get(id=download_id, user=user)
        except OfflineDownload.DoesNotExist:
            raise ValueError("Download não encontrado.")
        
        return {
            'id': download.id,
            'status': download.status,
            'progress': download.download_progress,
            'file_size': download.file_size,
            'error_message': download.error_message,
            'created_at': download.created_at,
            'completed_at': download.completed_at,
            'expires_at': download.expires_at,
            'is_available': download.is_available,
            'download_url': download.get_file_url(),
            'capitulo': {
                'title': download.capitulo.manga.title,
                'chapter_number': download.capitulo.number,
                'volume_number': download.capitulo.volume.number if download.capitulo.volume else None,
            }
        }
    
    def cancel_download(self, download_id: int, user: User) -> bool:
        """
        Cancela um download.
        """
        try:
            download = OfflineDownload.objects.get(id=download_id, user=user)
        except OfflineDownload.DoesNotExist:
            raise ValueError("Download não encontrado.")
        
        if download.status not in ['pending', 'downloading']:
            raise ValueError("Download não pode ser cancelado.")
        
        download.cancel_download()
        
        logger.info(f"Download cancelado: {download_id} por {user.username}")
        return True
    
    def delete_download(self, download_id: int, user: User) -> bool:
        """
        Remove um download concluído.
        """
        try:
            download = OfflineDownload.objects.get(id=download_id, user=user)
        except OfflineDownload.DoesNotExist:
            raise ValueError("Download não encontrado.")
        
        download.cleanup_file()
        download.delete()
        
        logger.info(f"Download removido: {download_id} por {user.username}")
        return True
    
    def get_download_stats(self, user: User) -> Dict[str, Any]:
        """
        Obtém estatísticas de downloads do usuário.
        """
        preferences = self._get_user_preferences(user)
        
        downloads = OfflineDownload.objects.filter(user=user)
        
        stats = {
            'total_downloads': downloads.count(),
            'completed_downloads': downloads.filter(status='completed').count(),
            'pending_downloads': downloads.filter(status='pending').count(),
            'failed_downloads': downloads.filter(status='failed').count(),
            'storage_used_mb': preferences.current_storage_usage,
            'storage_limit_mb': preferences.max_storage_size,
            'storage_usage_percentage': preferences.storage_usage_percentage,
        }
        
        return stats
    
    def cleanup_expired_downloads(self) -> int:
        """
        Remove downloads expirados.
        """
        expired_downloads = OfflineDownload.objects.filter(
            status='completed',
            expires_at__lt=timezone.now()
        )
        
        count = expired_downloads.count()
        
        for download in expired_downloads:
            download.cleanup_file()
        
        expired_downloads.delete()
        
        logger.info(f"Removidos {count} downloads expirados")
        return count
    
    def _start_download_async(self, download: OfflineDownload):
        """
        Inicia download em background (simulado).
        Em produção, use Celery ou similar.
        """
        try:
            # Marcar como baixando
            download.status = 'downloading'
            download.save()
            
            # Simular progresso
            for progress in range(0, 101, 10):
                download.download_progress = progress
                download.save()
                timezone.sleep(0.5)  # Simular tempo de download
            
            # Criar arquivo ZIP
            file_path, file_size = self._create_chapter_zip(download.capitulo, download.user)
            
            # Marcar como concluído
            download.mark_as_completed(file_path, file_size)
            
            logger.info(f"Download concluído: {download.id}")
            
        except Exception as e:
            logger.error(f"Erro no download {download.id}: {str(e)}")
            download.mark_as_failed(str(e))
    
    def _create_chapter_zip(self, capitulo: Capitulo, user: User) -> tuple:
        """
        Cria arquivo ZIP com as páginas do capítulo.
        """
        # Obter preferências do usuário
        preferences = self._get_user_preferences(user)
        
        # Criar arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            with zipfile.ZipFile(temp_file, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Adicionar páginas ao ZIP
                paginas = capitulo.paginas.all().order_by('number')
                
                for pagina in paginas:
                    if pagina.image:
                        # Processar imagem conforme qualidade
                        image_data = self._process_image_for_download(
                            pagina.image, 
                            preferences.download_quality
                        )
                        
                        # Nome do arquivo no ZIP
                        filename = f"page_{pagina.number:03d}.jpg"
                        
                        # Adicionar ao ZIP
                        zip_file.writestr(filename, image_data)
                
                # Adicionar arquivo de informações
                info_content = self._create_info_file(capitulo)
                zip_file.writestr('info.txt', info_content)
            
            # Mover para storage
            file_path = f"downloads/{user.id}/{capitulo.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.zip"
            
            with open(temp_file.name, 'rb') as f:
                default_storage.save(file_path, ContentFile(f.read()))
            
            # Obter tamanho do arquivo
            file_size = default_storage.size(file_path)
            
            # Limpar arquivo temporário
            os.unlink(temp_file.name)
            
            return file_path, file_size
    
    def _process_image_for_download(self, image_field, quality: str) -> bytes:
        """
        Processa imagem conforme qualidade solicitada.
        """
        # Abrir imagem
        with Image.open(image_field) as img:
            if quality == 'original':
                # Manter qualidade original
                output = io.BytesIO()
                img.save(output, format='JPEG', quality=95)
                return output.getvalue()
            
            elif quality == 'compressed':
                # Comprimir imagem
                if img.mode in ('RGBA', 'LA'):
                    img = img.convert('RGB')
                
                # Redimensionar se muito grande
                max_size = (1200, 1600)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                output = io.BytesIO()
                img.save(output, format='JPEG', quality=80, optimize=True)
                return output.getvalue()
            
            elif quality == 'web_optimized':
                # Otimizado para web
                if img.mode in ('RGBA', 'LA'):
                    img = img.convert('RGB')
                
                # Redimensionar para tamanho web
                max_size = (800, 1200)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                output = io.BytesIO()
                img.save(output, format='JPEG', quality=70, optimize=True)
                return output.getvalue()
            
            else:
                # Padrão
                output = io.BytesIO()
                img.save(output, format='JPEG', quality=85)
                return output.getvalue()
    
    def _create_info_file(self, capitulo: Capitulo) -> str:
        """
        Cria arquivo de informações do capítulo.
        """
        info = f"""Informações do Capítulo

Mangá: {capitulo.manga.title}
Capítulo: {capitulo.number}
Título: {capitulo.title or 'Sem título'}
Volume: {capitulo.volume.number if capitulo.volume else 'N/A'}
Autor: {capitulo.manga.author}
Páginas: {capitulo.paginas.count()}
Data de Publicação: {capitulo.created_at.strftime('%d/%m/%Y')}

Baixado em: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}

---
Project Nix - Sistema de Leitura de Mangá
"""
        return info
    
    def _estimate_download_size(self, capitulo: Capitulo, quality: str) -> float:
        """
        Estima o tamanho do download em MB.
        """
        total_pages = capitulo.paginas.count()
        
        # Tamanho estimado por página baseado na qualidade
        size_per_page = {
            'original': 2.5,      # ~2.5MB por página
            'compressed': 1.2,    # ~1.2MB por página
            'web_optimized': 0.8, # ~0.8MB por página
        }.get(quality, 1.5)
        
        estimated_size = total_pages * size_per_page
        
        # Adicionar overhead do ZIP
        estimated_size *= 0.9  # ZIP reduz tamanho
        
        return estimated_size
    
    def _get_user_preferences(self, user: User) -> DownloadPreferences:
        """
        Obtém ou cria preferências de download do usuário.
        """
        preferences, created = DownloadPreferences.objects.get_or_create(
            user=user,
            defaults={
                'max_storage_size': 1024,  # 1GB
                'keep_downloads_for_days': 30,
                'notify_on_completion': True,
            }
        )
        return preferences
    
    def get_download_queue_status(self, user: User) -> Dict[str, Any]:
        """
        Obtém status da fila de downloads do usuário.
        """
        queue = DownloadQueue.objects.filter(user=user, is_active=True).first()
        
        if not queue:
            return {
                'has_queue': False,
                'pending': 0,
                'active': 0,
                'completed': 0,
            }
        
        return {
            'has_queue': True,
            'queue_name': queue.name,
            'pending': queue.pending_downloads.count(),
            'active': queue.active_downloads.count(),
            'completed': queue.completed_downloads.count(),
            'max_concurrent': queue.max_concurrent_downloads,
        } 