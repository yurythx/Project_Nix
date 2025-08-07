from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import json
import os
import hashlib
import tempfile
from datetime import datetime, timedelta
from django.core.cache import cache
from ..services.batch_upload_service import BatchUploadService
from ..services.quality_service import QualityModerationService
from ..validators.file_validators import ImageFileValidator
import logging

logger = logging.getLogger(__name__)


class UploadSessionManager:
    """
    Gerencia sessões de upload resumível
    """
    
    def __init__(self):
        self.cache_timeout = 3600 * 24  # 24 horas
        self.temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_uploads')
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def create_session(self, filename, filesize, filetype, chunks, metadata=None):
        """
        Cria uma nova sessão de upload
        """
        session_id = self._generate_session_id(filename, filesize)
        upload_id = self._generate_upload_id()
        
        session_data = {
            'session_id': session_id,
            'upload_id': upload_id,
            'filename': filename,
            'filesize': filesize,
            'filetype': filetype,
            'total_chunks': chunks,
            'uploaded_chunks': [],
            'metadata': metadata or {},
            'created_at': datetime.now().isoformat(),
            'status': 'active',
            'temp_path': os.path.join(self.temp_dir, f"{session_id}_{upload_id}")
        }
        
        # Salva no cache
        cache_key = f"upload_session_{session_id}"
        cache.set(cache_key, session_data, self.cache_timeout)
        
        # Cria diretório temporário
        os.makedirs(session_data['temp_path'], exist_ok=True)
        
        return session_data
    
    def get_session(self, session_id):
        """
        Obtém dados da sessão
        """
        cache_key = f"upload_session_{session_id}"
        return cache.get(cache_key)
    
    def update_session(self, session_id, data):
        """
        Atualiza dados da sessão
        """
        cache_key = f"upload_session_{session_id}"
        session_data = cache.get(cache_key)
        
        if session_data:
            session_data.update(data)
            cache.set(cache_key, session_data, self.cache_timeout)
            return session_data
        
        return None
    
    def delete_session(self, session_id):
        """
        Remove sessão e arquivos temporários
        """
        session_data = self.get_session(session_id)
        
        if session_data:
            # Remove arquivos temporários
            temp_path = session_data.get('temp_path')
            if temp_path and os.path.exists(temp_path):
                try:
                    import shutil
                    shutil.rmtree(temp_path)
                except Exception as e:
                    logger.error(f"Erro ao remover diretório temporário {temp_path}: {e}")
            
            # Remove do cache
            cache_key = f"upload_session_{session_id}"
            cache.delete(cache_key)
            
            return True
        
        return False
    
    def add_chunk(self, session_id, chunk_index, chunk_data):
        """
        Adiciona um chunk à sessão
        """
        session_data = self.get_session(session_id)
        
        if not session_data:
            raise ValueError("Sessão não encontrada")
        
        # Salva chunk no diretório temporário
        chunk_path = os.path.join(
            session_data['temp_path'], 
            f"chunk_{chunk_index:06d}"
        )
        
        with open(chunk_path, 'wb') as f:
            f.write(chunk_data)
        
        # Atualiza lista de chunks
        uploaded_chunks = session_data.get('uploaded_chunks', [])
        if chunk_index not in uploaded_chunks:
            uploaded_chunks.append(chunk_index)
            uploaded_chunks.sort()
        
        self.update_session(session_id, {
            'uploaded_chunks': uploaded_chunks,
            'last_chunk_at': datetime.now().isoformat()
        })
        
        return True
    
    def finalize_upload(self, session_id, upload_id):
        """
        Finaliza o upload juntando todos os chunks
        """
        session_data = self.get_session(session_id)
        
        if not session_data:
            raise ValueError("Sessão não encontrada")
        
        if session_data['upload_id'] != upload_id:
            raise ValueError("Upload ID inválido")
        
        # Verifica se todos os chunks foram enviados
        expected_chunks = list(range(session_data['total_chunks']))
        uploaded_chunks = session_data.get('uploaded_chunks', [])
        
        if set(uploaded_chunks) != set(expected_chunks):
            missing_chunks = set(expected_chunks) - set(uploaded_chunks)
            raise ValueError(f"Chunks faltando: {missing_chunks}")
        
        # Junta os chunks
        final_file_path = self._assemble_chunks(session_data)
        
        # Atualiza sessão
        self.update_session(session_id, {
            'status': 'completed',
            'final_file_path': final_file_path,
            'completed_at': datetime.now().isoformat()
        })
        
        return final_file_path
    
    def _assemble_chunks(self, session_data):
        """
        Junta todos os chunks em um arquivo final
        """
        temp_path = session_data['temp_path']
        filename = session_data['filename']
        
        # Cria arquivo final
        final_filename = f"{session_data['upload_id']}_{filename}"
        final_path = os.path.join(self.temp_dir, final_filename)
        
        with open(final_path, 'wb') as final_file:
            for chunk_index in sorted(session_data['uploaded_chunks']):
                chunk_path = os.path.join(temp_path, f"chunk_{chunk_index:06d}")
                
                if os.path.exists(chunk_path):
                    with open(chunk_path, 'rb') as chunk_file:
                        final_file.write(chunk_file.read())
                else:
                    raise ValueError(f"Chunk {chunk_index} não encontrado")
        
        return final_path
    
    def _generate_session_id(self, filename, filesize):
        """
        Gera ID único para a sessão
        """
        data = f"{filename}_{filesize}_{datetime.now().isoformat()}"
        return hashlib.md5(data.encode()).hexdigest()
    
    def _generate_upload_id(self):
        """
        Gera ID único para o upload
        """
        return hashlib.sha256(str(datetime.now().timestamp()).encode()).hexdigest()[:16]
    
    def cleanup_expired_sessions(self):
        """
        Remove sessões expiradas (chamado por task periódica)
        """
        # Esta função seria chamada por uma task do Celery
        # Por simplicidade, não implementamos aqui
        pass


# Instância global do gerenciador
session_manager = UploadSessionManager()


@method_decorator(csrf_exempt, name='dispatch')
class ResumableUploadSessionView(View):
    """
    API para gerenciar sessões de upload resumível
    """
    
    def post(self, request):
        """
        Cria uma nova sessão de upload
        """
        try:
            data = json.loads(request.body)
            
            filename = data.get('filename')
            filesize = data.get('filesize')
            filetype = data.get('filetype')
            chunks = data.get('chunks')
            metadata = data.get('metadata', {})
            
            # Validações básicas
            if not all([filename, filesize, filetype, chunks]):
                return JsonResponse({
                    'error': 'Parâmetros obrigatórios: filename, filesize, filetype, chunks'
                }, status=400)
            
            # Validação de tamanho
            max_size = 20 * 1024 * 1024  # 20MB
            if filesize > max_size:
                return JsonResponse({
                    'error': f'Arquivo muito grande. Máximo: {max_size // (1024*1024)}MB'
                }, status=400)
            
            # Cria sessão
            session_data = session_manager.create_session(
                filename, filesize, filetype, chunks, metadata
            )
            
            return JsonResponse({
                'session_id': session_data['session_id'],
                'upload_id': session_data['upload_id'],
                'status': 'created'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        except Exception as e:
            logger.error(f"Erro ao criar sessão: {e}")
            return JsonResponse({'error': 'Erro interno do servidor'}, status=500)
    
    def get(self, request, session_id=None):
        """
        Obtém informações da sessão
        """
        if not session_id:
            return JsonResponse({'error': 'Session ID obrigatório'}, status=400)
        
        session_data = session_manager.get_session(session_id)
        
        if not session_data:
            return JsonResponse({'error': 'Sessão não encontrada'}, status=404)
        
        return JsonResponse({
            'session_id': session_data['session_id'],
            'upload_id': session_data['upload_id'],
            'filename': session_data['filename'],
            'filesize': session_data['filesize'],
            'total_chunks': session_data['total_chunks'],
            'uploaded_chunks': session_data.get('uploaded_chunks', []),
            'status': session_data.get('status', 'active'),
            'progress': len(session_data.get('uploaded_chunks', [])) / session_data['total_chunks'] * 100
        })
    
    def delete(self, request, session_id=None):
        """
        Cancela e remove sessão
        """
        if not session_id:
            return JsonResponse({'error': 'Session ID obrigatório'}, status=400)
        
        success = session_manager.delete_session(session_id)
        
        if success:
            return JsonResponse({'status': 'deleted'})
        else:
            return JsonResponse({'error': 'Sessão não encontrada'}, status=404)


@method_decorator(csrf_exempt, name='dispatch')
class ResumableChunkUploadView(View):
    """
    API para upload de chunks individuais
    """
    
    def post(self, request):
        """
        Recebe um chunk de arquivo
        """
        try:
            session_id = request.POST.get('session_id')
            upload_id = request.POST.get('upload_id')
            chunk_index = int(request.POST.get('chunk_index', 0))
            chunk_size = int(request.POST.get('chunk_size', 0))
            chunk_data = request.FILES.get('chunk_data')
            
            # Validações
            if not all([session_id, upload_id, chunk_data]):
                return JsonResponse({
                    'error': 'Parâmetros obrigatórios: session_id, upload_id, chunk_data'
                }, status=400)
            
            # Verifica sessão
            session_data = session_manager.get_session(session_id)
            if not session_data:
                return JsonResponse({'error': 'Sessão não encontrada'}, status=404)
            
            if session_data['upload_id'] != upload_id:
                return JsonResponse({'error': 'Upload ID inválido'}, status=400)
            
            # Verifica se chunk já foi enviado
            uploaded_chunks = session_data.get('uploaded_chunks', [])
            if chunk_index in uploaded_chunks:
                return JsonResponse({
                    'status': 'already_uploaded',
                    'chunk_index': chunk_index
                })
            
            # Lê dados do chunk
            chunk_bytes = chunk_data.read()
            
            # Verifica tamanho
            if len(chunk_bytes) != chunk_size:
                return JsonResponse({
                    'error': f'Tamanho do chunk inválido. Esperado: {chunk_size}, Recebido: {len(chunk_bytes)}'
                }, status=400)
            
            # Salva chunk
            session_manager.add_chunk(session_id, chunk_index, chunk_bytes)
            
            # Calcula progresso
            updated_session = session_manager.get_session(session_id)
            progress = len(updated_session['uploaded_chunks']) / updated_session['total_chunks'] * 100
            
            return JsonResponse({
                'status': 'uploaded',
                'chunk_index': chunk_index,
                'progress': progress,
                'uploaded_chunks': len(updated_session['uploaded_chunks']),
                'total_chunks': updated_session['total_chunks']
            })
            
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            logger.error(f"Erro ao fazer upload do chunk: {e}")
            return JsonResponse({'error': 'Erro interno do servidor'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ResumableUploadFinalizeView(View):
    """
    API para finalizar upload resumível
    """
    
    def post(self, request, session_id=None):
        """
        Finaliza o upload juntando todos os chunks
        """
        try:
            if not session_id:
                return JsonResponse({'error': 'Session ID obrigatório'}, status=400)
            
            data = json.loads(request.body)
            upload_id = data.get('upload_id')
            
            if not upload_id:
                return JsonResponse({'error': 'Upload ID obrigatório'}, status=400)
            
            # Finaliza upload
            final_file_path = session_manager.finalize_upload(session_id, upload_id)
            
            # Processa arquivo final
            session_data = session_manager.get_session(session_id)
            
            # Valida arquivo final
            validator = ImageFileValidator()
            
            with open(final_file_path, 'rb') as f:
                temp_file = ContentFile(f.read(), name=session_data['filename'])
                
                try:
                    validator.validate(temp_file)
                except Exception as validation_error:
                    # Remove arquivo inválido
                    os.remove(final_file_path)
                    session_manager.delete_session(session_id)
                    
                    return JsonResponse({
                        'error': f'Arquivo inválido: {validation_error}'
                    }, status=400)
            
            # Move arquivo para local final
            final_filename = f"uploads/{datetime.now().strftime('%Y/%m/%d')}/{session_data['filename']}"
            final_url = default_storage.save(final_filename, ContentFile(open(final_file_path, 'rb').read()))
            
            # Remove arquivo temporário
            os.remove(final_file_path)
            
            # Análise de qualidade (opcional)
            quality_score = None
            try:
                quality_service = QualityModerationService()
                with default_storage.open(final_url, 'rb') as f:
                    temp_file = ContentFile(f.read(), name=session_data['filename'])
                    quality_analysis = quality_service.analyze_image_quality(temp_file)
                    quality_score = quality_analysis.get('overall_score', 0)
            except Exception as e:
                logger.warning(f"Erro na análise de qualidade: {e}")
            
            # Limpa sessão
            session_manager.delete_session(session_id)
            
            return JsonResponse({
                'status': 'completed',
                'file_url': final_url,
                'file_id': upload_id,
                'filename': session_data['filename'],
                'filesize': session_data['filesize'],
                'quality_score': quality_score
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            logger.error(f"Erro ao finalizar upload: {e}")
            return JsonResponse({'error': 'Erro interno do servidor'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ResumableUploadChunksView(View):
    """
    API para verificar chunks já enviados
    """
    
    def get(self, request, session_id=None):
        """
        Retorna lista de chunks já enviados
        """
        if not session_id:
            return JsonResponse({'error': 'Session ID obrigatório'}, status=400)
        
        session_data = session_manager.get_session(session_id)
        
        if not session_data:
            return JsonResponse({'error': 'Sessão não encontrada'}, status=404)
        
        return JsonResponse({
            'session_id': session_id,
            'uploaded_chunks': session_data.get('uploaded_chunks', []),
            'total_chunks': session_data['total_chunks'],
            'progress': len(session_data.get('uploaded_chunks', [])) / session_data['total_chunks'] * 100
        })