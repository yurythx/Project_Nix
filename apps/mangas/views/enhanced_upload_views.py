from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.generic import CreateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.db import transaction
from django.conf import settings
import json
import uuid
import logging
from typing import List, Dict, Any

from ..models import Manga, Capitulo, Pagina
from ..forms.unified_forms import UnifiedCapituloCompleteForm
from ..services.batch_upload_service import BatchUploadService, UploadSession
from ..services.quality_service import QualityModerationService
from ..validators.file_validators import ImageFileValidator
from ..constants.file_limits import (
    MAX_UPLOAD_SIZE_MB, MAX_SESSION_SIZE_MB, MAX_FILES_PER_SESSION,
    MIN_IMAGE_WIDTH, MIN_IMAGE_HEIGHT, MAX_IMAGE_WIDTH, MAX_IMAGE_HEIGHT
)

logger = logging.getLogger(__name__)


class EnhancedUploadView(LoginRequiredMixin, CreateView):
    """
    View principal para o sistema de upload aprimorado.
    
    Implementa a melhoria 5 (interface de upload aprimorada) com:
    - Interface moderna com drag & drop
    - Validação instantânea
    - Preview de imagens
    - Sessões de upload
    """
    model = Capitulo
    form_class = UnifiedCapituloCompleteForm
    template_name = 'mangas/enhanced_upload_form.html'
    success_url = reverse_lazy('mangas:manga_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Adiciona informações do mangá se especificado
        manga_id = self.request.GET.get('manga_id')
        if manga_id:
            try:
                manga = get_object_or_404(Manga, id=manga_id)
                context['manga'] = manga
                context['form'].fields['manga'].initial = manga
            except (ValueError, Manga.DoesNotExist):
                pass
        
        # Adiciona configurações de upload
        context['upload_config'] = {
            'max_file_size': MAX_UPLOAD_SIZE_MB * 1024 * 1024,
            'max_session_size': MAX_SESSION_SIZE_MB * 1024 * 1024,
            'max_files': MAX_FILES_PER_SESSION,
            'min_width': MIN_IMAGE_WIDTH,
            'min_height': MIN_IMAGE_HEIGHT,
            'max_width': MAX_IMAGE_WIDTH,
            'max_height': MAX_IMAGE_HEIGHT,
        }
        
        return context
    
    def post(self, request, *args, **kwargs):
        """
        Processa o upload usando o BatchUploadService.
        """
        try:
            # Verifica se é uma requisição AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return self.handle_ajax_upload(request)
            else:
                return super().post(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Erro no upload: {str(e)}", exc_info=True)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=500)
            else:
                messages.error(request, f"Erro no upload: {str(e)}")
                return self.form_invalid(self.get_form())
    
    def handle_ajax_upload(self, request):
        """
        Processa upload via AJAX usando o BatchUploadService.
        """
        form = self.get_form()
        
        if not form.is_valid():
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
        
        # Obtém arquivos de imagem
        image_files = request.FILES.getlist('images')
        if not image_files:
            return JsonResponse({
                'success': False,
                'error': 'Nenhuma imagem foi enviada'
            }, status=400)
        
        # Obtém ID da sessão
        session_id = request.POST.get('session_id')
        
        try:
            # Usa o BatchUploadService para processar
            batch_service = BatchUploadService()
            
            # Cria ou recupera sessão
            if session_id:
                upload_session = batch_service.get_session(session_id)
                if not upload_session:
                    return JsonResponse({
                        'success': False,
                        'error': 'Sessão de upload inválida'
                    }, status=400)
            else:
                upload_session = batch_service.create_session(
                    user=request.user,
                    manga_id=form.cleaned_data['manga'].id
                )
            
            # Processa upload em lote
            with transaction.atomic():
                result = batch_service.process_batch_upload(
                    session=upload_session,
                    files=image_files,
                    chapter_data={
                        'manga': form.cleaned_data['manga'],
                        'numero': form.cleaned_data['numero'],
                        'titulo': form.cleaned_data.get('titulo', ''),
                        'volume': form.cleaned_data.get('volume'),
                        'data_publicacao': form.cleaned_data.get('data_publicacao'),
                        'descricao': form.cleaned_data.get('descricao', ''),
                        'usuario': request.user
                    }
                )
            
            # Retorna resultado
            if result['success']:
                capitulo = result['chapter']
                return JsonResponse({
                    'success': True,
                    'message': f'Capítulo {capitulo.numero} criado com sucesso!',
                    'chapter_id': capitulo.id,
                    'redirect_url': capitulo.get_absolute_url(),
                    'stats': result['stats']
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': result['error'],
                    'details': result.get('details', [])
                }, status=400)
                
        except Exception as e:
            logger.error(f"Erro no processamento em lote: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': f'Erro interno: {str(e)}'
            }, status=500)


class UploadSessionAPIView(LoginRequiredMixin, View):
    """
    API para gerenciar sessões de upload.
    
    Endpoints:
    - POST: Criar nova sessão
    - GET: Obter informações da sessão
    - DELETE: Cancelar sessão
    """
    
    def post(self, request):
        """
        Cria uma nova sessão de upload.
        """
        try:
            data = json.loads(request.body)
            manga_id = data.get('manga_id')
            volume_id = data.get('volume_id')
            
            batch_service = BatchUploadService()
            session = batch_service.create_session(
                user=request.user,
                manga_id=manga_id,
                volume_id=volume_id
            )
            
            return JsonResponse({
                'success': True,
                'session_id': session.session_id,
                'created_at': session.created_at.isoformat(),
                'limits': {
                    'max_file_size': MAX_UPLOAD_SIZE_MB * 1024 * 1024,
                    'max_session_size': MAX_SESSION_SIZE_MB * 1024 * 1024,
                    'max_files': MAX_FILES_PER_SESSION
                }
            })
            
        except Exception as e:
            logger.error(f"Erro ao criar sessão: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def get(self, request):
        """
        Obtém informações de uma sessão.
        """
        session_id = request.GET.get('session_id')
        if not session_id:
            return JsonResponse({
                'success': False,
                'error': 'session_id é obrigatório'
            }, status=400)
        
        try:
            batch_service = BatchUploadService()
            session = batch_service.get_session(session_id)
            
            if not session:
                return JsonResponse({
                    'success': False,
                    'error': 'Sessão não encontrada'
                }, status=404)
            
            return JsonResponse({
                'success': True,
                'session': {
                    'session_id': session.session_id,
                    'status': session.status,
                    'created_at': session.created_at.isoformat(),
                    'file_count': len(session.files),
                    'total_size': session.total_size,
                    'manga_id': session.manga_id,
                    'volume_id': session.volume_id
                }
            })
            
        except Exception as e:
            logger.error(f"Erro ao obter sessão: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def delete(self, request):
        """
        Cancela uma sessão de upload.
        """
        try:
            data = json.loads(request.body)
            session_id = data.get('session_id')
            
            if not session_id:
                return JsonResponse({
                    'success': False,
                    'error': 'session_id é obrigatório'
                }, status=400)
            
            batch_service = BatchUploadService()
            success = batch_service.cancel_session(session_id)
            
            if success:
                return JsonResponse({
                    'success': True,
                    'message': 'Sessão cancelada com sucesso'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Sessão não encontrada ou já finalizada'
                }, status=404)
                
        except Exception as e:
            logger.error(f"Erro ao cancelar sessão: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


class FileValidationAPIView(LoginRequiredMixin, View):
    """
    API para validação de arquivos antes do upload.
    
    Permite validação prévia dos arquivos sem fazer upload,
    incluindo análise de qualidade e detecção de duplicatas.
    """
    
    def post(self, request):
        """
        Valida arquivos enviados.
        """
        try:
            files = request.FILES.getlist('files')
            if not files:
                return JsonResponse({
                    'success': False,
                    'error': 'Nenhum arquivo enviado para validação'
                }, status=400)
            
            # Serviços
            batch_service = BatchUploadService()
            quality_service = QualityModerationService()
            
            results = []
            total_size = 0
            
            for file in files:
                try:
                    # Validação básica
                    validator = ImageFileValidator()
                    validation_result = {
                        'filename': file.name,
                        'size': file.size,
                        'valid': True,
                        'errors': [],
                        'warnings': [],
                        'quality': None
                    }
                    
                    # Valida arquivo
                    try:
                        validator.validate(file)
                    except ValidationError as e:
                        validation_result['valid'] = False
                        validation_result['errors'].extend(e.messages)
                    
                    # Análise de qualidade (se válido)
                    if validation_result['valid']:
                        try:
                            quality_analysis = quality_service.analyze_image_quality(file)
                            validation_result['quality'] = quality_analysis
                            
                            # Adiciona avisos baseados na qualidade
                            if quality_analysis.get('score', 0) < 0.7:
                                validation_result['warnings'].append(
                                    'Qualidade da imagem pode ser melhorada'
                                )
                            
                            # Verifica duplicatas
                            manga_id = request.POST.get('manga_id')
                            if manga_id:
                                is_duplicate = quality_service.check_duplicate(
                                    file, manga_id
                                )
                                if is_duplicate:
                                    validation_result['warnings'].append(
                                        'Possível imagem duplicada detectada'
                                    )
                                    
                        except Exception as e:
                            logger.warning(f"Erro na análise de qualidade: {str(e)}")
                            validation_result['warnings'].append(
                                'Não foi possível analisar a qualidade da imagem'
                            )
                    
                    results.append(validation_result)
                    total_size += file.size
                    
                except Exception as e:
                    logger.error(f"Erro na validação de {file.name}: {str(e)}")
                    results.append({
                        'filename': file.name,
                        'size': file.size,
                        'valid': False,
                        'errors': [f'Erro na validação: {str(e)}'],
                        'warnings': [],
                        'quality': None
                    })
            
            # Validação de limites da sessão
            session_validation = batch_service.validate_session_limits(
                file_count=len(files),
                total_size=total_size
            )
            
            # Estatísticas
            valid_files = [r for r in results if r['valid']]
            invalid_files = [r for r in results if not r['valid']]
            
            return JsonResponse({
                'success': True,
                'results': results,
                'summary': {
                    'total_files': len(files),
                    'valid_files': len(valid_files),
                    'invalid_files': len(invalid_files),
                    'total_size': total_size,
                    'can_upload': len(valid_files) > 0 and session_validation['valid']
                },
                'session_validation': session_validation
            })
            
        except Exception as e:
            logger.error(f"Erro na validação de arquivos: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


class QualityAnalysisAPIView(LoginRequiredMixin, View):
    """
    API para análise de qualidade de imagens.
    
    Implementa parte da melhoria 6 (sistema de qualidade).
    """
    
    def post(self, request):
        """
        Analisa a qualidade de uma imagem.
        """
        try:
            file = request.FILES.get('image')
            if not file:
                return JsonResponse({
                    'success': False,
                    'error': 'Nenhuma imagem enviada'
                }, status=400)
            
            quality_service = QualityModerationService()
            
            # Análise completa
            analysis = quality_service.analyze_image_quality(file)
            
            # Verifica duplicatas se manga_id fornecido
            manga_id = request.POST.get('manga_id')
            duplicate_info = None
            if manga_id:
                duplicate_info = quality_service.check_duplicate(
                    file, manga_id, return_details=True
                )
            
            # Recomendações de moderação
            moderation = quality_service.get_moderation_recommendation(
                analysis, duplicate_info
            )
            
            return JsonResponse({
                'success': True,
                'analysis': analysis,
                'duplicate_info': duplicate_info,
                'moderation': moderation
            })
            
        except Exception as e:
            logger.error(f"Erro na análise de qualidade: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


class UploadStatsAPIView(LoginRequiredMixin, View):
    """
    API para estatísticas de upload.
    """
    
    def get(self, request):
        """
        Retorna estatísticas de upload do usuário.
        """
        try:
            # Estatísticas básicas
            user_chapters = Capitulo.objects.filter(usuario=request.user)
            user_pages = Pagina.objects.filter(capitulo__usuario=request.user)
            
            stats = {
                'total_chapters': user_chapters.count(),
                'total_pages': user_pages.count(),
                'total_mangas': user_chapters.values('manga').distinct().count(),
                'recent_uploads': []
            }
            
            # Uploads recentes
            recent_chapters = user_chapters.order_by('-data_criacao')[:10]
            for chapter in recent_chapters:
                stats['recent_uploads'].append({
                    'id': chapter.id,
                    'manga': chapter.manga.titulo,
                    'numero': chapter.numero,
                    'titulo': chapter.titulo,
                    'pages': chapter.paginas.count(),
                    'created_at': chapter.data_criacao.isoformat()
                })
            
            return JsonResponse({
                'success': True,
                'stats': stats
            })
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


# View de compatibilidade com o sistema existente
class EnhancedCapituloCreateView(EnhancedUploadView):
    """
    View de compatibilidade que mantém a interface existente
    mas usa o sistema aprimorado por baixo.
    """
    template_name = 'mangas/capitulo_complete_form.html'
    
    def get_template_names(self):
        # Usa template aprimorado se disponível
        if self.request.GET.get('enhanced') == '1':
            return ['mangas/enhanced_upload_form.html']
        return [self.template_name]