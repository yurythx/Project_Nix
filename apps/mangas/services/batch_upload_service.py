"""Serviço de upload em lote aprimorado para mangás.

Este módulo implementa as melhorias 3 (processamento em lote aprimorado)
com sessões de upload, validação prévia, upload assíncrono e rollback.
"""

import os
import uuid
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from django.core.cache import cache
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from PIL import Image
import hashlib

from ..models.manga import Manga
from ..models.volume import Volume
from ..models.capitulo import Capitulo
from ..models.pagina import Pagina
from ..validators.file_validators import ImageFileValidator, ArchiveFileValidator
from ..constants.file_limits import (
    MAX_UPLOAD_SIZE_MB, MAX_PAGES_PER_CHAPTER,
    ALLOWED_IMAGE_EXTENSIONS, ALLOWED_ARCHIVE_EXTENSIONS
)
from ..exceptions import (
    MangaException, InvalidFileError, FileTooLargeError,
    UnsupportedFileTypeError
)

logger = logging.getLogger(__name__)

# Novos limites aprimorados baseados nas melhores práticas
MAX_FILE_SIZE_MB = 20  # 20MB por arquivo
MAX_SESSION_SIZE_MB = 200  # 200MB por sessão
MAX_FILES_PER_SESSION = 500  # 500 arquivos por sessão
SESSION_TIMEOUT_HOURS = 24  # 24 horas
MAX_DIMENSION_PIXELS = 10000  # 10.000 pixels máximo
MIN_WIDTH = 800  # 800px mínimo
MIN_HEIGHT = 1200  # 1200px mínimo

class UploadSession:
    """Representa uma sessão de upload com estado persistente."""
    
    def __init__(self, session_id: str = None, user_id: int = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.user_id = user_id
        self.created_at = timezone.now()
        self.files = []
        self.total_size = 0
        self.status = 'created'
        self.errors = []
        self.processed_files = 0
        self.manga_id = None
        self.volume_id = None
        self.chapter_id = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte a sessão para dicionário para cache."""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'files': self.files,
            'total_size': self.total_size,
            'status': self.status,
            'errors': self.errors,
            'processed_files': self.processed_files,
            'manga_id': self.manga_id,
            'volume_id': self.volume_id,
            'chapter_id': self.chapter_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UploadSession':
        """Cria uma sessão a partir de dicionário do cache."""
        session = cls(data['session_id'], data['user_id'])
        session.created_at = datetime.fromisoformat(data['created_at'])
        session.files = data['files']
        session.total_size = data['total_size']
        session.status = data['status']
        session.errors = data['errors']
        session.processed_files = data['processed_files']
        session.manga_id = data['manga_id']
        session.volume_id = data['volume_id']
        session.chapter_id = data['chapter_id']
        return session

class BatchUploadService:
    """Serviço de upload em lote aprimorado."""
    
    def __init__(self):
        self.image_validator = ImageFileValidator(
            min_width=MIN_WIDTH,
            min_height=MIN_HEIGHT,
            max_width=MAX_DIMENSION_PIXELS,
            max_height=MAX_DIMENSION_PIXELS
        )
        self.archive_validator = ArchiveFileValidator()
    
    def create_upload_session(self, user_id: int, manga_id: int = None, 
                            volume_id: int = None) -> UploadSession:
        """Cria uma nova sessão de upload."""
        session = UploadSession(user_id=user_id)
        session.manga_id = manga_id
        session.volume_id = volume_id
        
        # Salva no cache
        cache_key = f"upload_session:{session.session_id}"
        cache.set(cache_key, session.to_dict(), timeout=SESSION_TIMEOUT_HOURS * 3600)
        
        logger.info(f"Sessão de upload criada: {session.session_id} para usuário {user_id}")
        return session
    
    def get_upload_session(self, session_id: str) -> Optional[UploadSession]:
        """Recupera uma sessão de upload do cache."""
        cache_key = f"upload_session:{session_id}"
        data = cache.get(cache_key)
        
        if not data:
            return None
        
        return UploadSession.from_dict(data)
    
    def validate_files_preview(self, files: List[UploadedFile], 
                             session_id: str) -> Dict[str, Any]:
        """Validação prévia dos arquivos antes do upload."""
        session = self.get_upload_session(session_id)
        if not session:
            raise MangaException("Sessão de upload não encontrada")
        
        validation_results = {
            'valid_files': [],
            'invalid_files': [],
            'warnings': [],
            'total_size': 0,
            'estimated_pages': 0,
            'duplicates': []
        }
        
        # Verifica limites da sessão
        if len(files) > MAX_FILES_PER_SESSION:
            validation_results['warnings'].append(
                f"Muitos arquivos selecionados. Máximo: {MAX_FILES_PER_SESSION}"
            )
        
        total_size = sum(f.size for f in files)
        if total_size > MAX_SESSION_SIZE_MB * 1024 * 1024:
            validation_results['warnings'].append(
                f"Tamanho total excede o limite. Máximo: {MAX_SESSION_SIZE_MB}MB"
            )
        
        # Detecta duplicatas por hash
        file_hashes = {}
        
        for file in files:
            try:
                # Validação básica de tamanho
                if file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
                    validation_results['invalid_files'].append({
                        'name': file.name,
                        'error': f"Arquivo muito grande (máximo {MAX_FILE_SIZE_MB}MB)"
                    })
                    continue
                
                # Calcula hash para detectar duplicatas
                file_hash = self._calculate_file_hash(file)
                if file_hash in file_hashes:
                    validation_results['duplicates'].append({
                        'name': file.name,
                        'duplicate_of': file_hashes[file_hash]
                    })
                    continue
                
                file_hashes[file_hash] = file.name
                
                # Validação específica por tipo
                file_info = self._validate_single_file(file)
                if file_info['valid']:
                    validation_results['valid_files'].append(file_info)
                    validation_results['estimated_pages'] += file_info.get('estimated_pages', 1)
                else:
                    validation_results['invalid_files'].append({
                        'name': file.name,
                        'error': file_info['error']
                    })
                
            except Exception as e:
                logger.error(f"Erro na validação prévia de {file.name}: {e}")
                validation_results['invalid_files'].append({
                    'name': file.name,
                    'error': f"Erro na validação: {str(e)}"
                })
        
        validation_results['total_size'] = total_size
        return validation_results
    
    def _validate_single_file(self, file: UploadedFile) -> Dict[str, Any]:
        """Valida um único arquivo."""
        file_info = {
            'name': file.name,
            'size': file.size,
            'type': 'unknown',
            'valid': False,
            'error': None,
            'estimated_pages': 1,
            'dimensions': None,
            'aspect_ratio': None
        }
        
        try:
            ext = os.path.splitext(file.name)[1].lower().replace('.', '')
            
            if ext in ALLOWED_IMAGE_EXTENSIONS:
                file_info['type'] = 'image'
                self.image_validator(file)
                
                # Analisa dimensões e aspect ratio
                with Image.open(file) as img:
                    width, height = img.size
                    file_info['dimensions'] = {'width': width, 'height': height}
                    file_info['aspect_ratio'] = round(height / width, 2)
                    
                    # Verifica aspect ratio típico de mangá (1.4-1.6)
                    if not (1.2 <= file_info['aspect_ratio'] <= 1.8):
                        file_info['warnings'] = file_info.get('warnings', [])
                        file_info['warnings'].append(
                            f"Aspect ratio incomum: {file_info['aspect_ratio']:.2f}"
                        )
                
                file_info['valid'] = True
                
            elif ext in ALLOWED_ARCHIVE_EXTENSIONS:
                file_info['type'] = 'archive'
                self.archive_validator(file)
                
                # Estima número de páginas no arquivo
                estimated_pages = self._estimate_archive_pages(file)
                file_info['estimated_pages'] = estimated_pages
                file_info['valid'] = True
                
            else:
                file_info['error'] = f"Tipo de arquivo não suportado: {ext}"
                
        except Exception as e:
            file_info['error'] = str(e)
        
        return file_info
    
    def _estimate_archive_pages(self, file: UploadedFile) -> int:
        """Estima o número de páginas em um arquivo compactado."""
        try:
            import zipfile
            import rarfile
            
            ext = os.path.splitext(file.name)[1].lower()
            
            if ext in ['.zip', '.cbz']:
                with zipfile.ZipFile(file) as zf:
                    image_files = [f for f in zf.namelist() 
                                 if any(f.lower().endswith(img_ext) 
                                       for img_ext in ['.jpg', '.jpeg', '.png', '.webp'])]
                    return len(image_files)
            
            elif ext in ['.rar', '.cbr']:
                with rarfile.RarFile(file) as rf:
                    image_files = [f for f in rf.namelist() 
                                 if any(f.lower().endswith(img_ext) 
                                       for img_ext in ['.jpg', '.jpeg', '.png', '.webp'])]
                    return len(image_files)
            
        except Exception as e:
            logger.warning(f"Erro ao estimar páginas de {file.name}: {e}")
        
        return 1  # Fallback
    
    def _calculate_file_hash(self, file: UploadedFile) -> str:
        """Calcula hash MD5 do arquivo para detectar duplicatas."""
        hash_md5 = hashlib.md5()
        for chunk in file.chunks():
            hash_md5.update(chunk)
        file.seek(0)  # Reset file pointer
        return hash_md5.hexdigest()
    
    def add_files_to_session(self, session_id: str, files: List[UploadedFile]) -> Dict[str, Any]:
        """Adiciona arquivos validados à sessão."""
        session = self.get_upload_session(session_id)
        if not session:
            raise MangaException("Sessão de upload não encontrada")
        
        validation_results = self.validate_files_preview(files, session_id)
        
        # Adiciona apenas arquivos válidos
        for file_info in validation_results['valid_files']:
            session.files.append(file_info)
            session.total_size += file_info['size']
        
        session.status = 'files_added'
        
        # Atualiza no cache
        cache_key = f"upload_session:{session_id}"
        cache.set(cache_key, session.to_dict(), timeout=SESSION_TIMEOUT_HOURS * 3600)
        
        return {
            'session': session,
            'validation_results': validation_results
        }
    
    def process_session_async(self, session_id: str, chapter_data: Dict[str, Any]) -> str:
        """Inicia processamento assíncrono da sessão."""
        from ..tasks.manga_tasks import process_batch_upload_task
        
        session = self.get_upload_session(session_id)
        if not session:
            raise MangaException("Sessão de upload não encontrada")
        
        session.status = 'processing'
        session.chapter_id = chapter_data.get('chapter_id')
        
        # Atualiza no cache
        cache_key = f"upload_session:{session_id}"
        cache.set(cache_key, session.to_dict(), timeout=SESSION_TIMEOUT_HOURS * 3600)
        
        # Inicia task assíncrona
        task = process_batch_upload_task.delay(session_id, chapter_data)
        
        logger.info(f"Processamento assíncrono iniciado para sessão {session_id}: {task.id}")
        return task.id
    
    def rollback_session(self, session_id: str) -> bool:
        """Faz rollback de uma sessão em caso de erro."""
        session = self.get_upload_session(session_id)
        if not session:
            return False
        
        try:
            with transaction.atomic():
                # Remove capítulo criado se existir
                if session.chapter_id:
                    try:
                        chapter = Capitulo.objects.get(id=session.chapter_id)
                        # Remove páginas associadas
                        chapter.paginas.all().delete()
                        # Remove capítulo
                        chapter.delete()
                        logger.info(f"Capítulo {session.chapter_id} removido no rollback")
                    except Capitulo.DoesNotExist:
                        pass
                
                # Marca sessão como falha
                session.status = 'failed'
                cache_key = f"upload_session:{session_id}"
                cache.set(cache_key, session.to_dict(), timeout=3600)  # Mantém por 1h para debug
                
                return True
                
        except Exception as e:
            logger.error(f"Erro no rollback da sessão {session_id}: {e}")
            return False
    
    def cleanup_expired_sessions(self) -> int:
        """Remove sessões expiradas do cache."""
        # Esta função seria chamada por uma task periódica
        # Por enquanto, retorna 0 como placeholder
        return 0
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Retorna o status atual da sessão."""
        session = self.get_upload_session(session_id)
        if not session:
            return {'status': 'not_found'}
        
        return {
            'status': session.status,
            'processed_files': session.processed_files,
            'total_files': len(session.files),
            'errors': session.errors,
            'progress_percentage': (session.processed_files / len(session.files) * 100) if session.files else 0
        }