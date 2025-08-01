import os
import logging
import tempfile
from pathlib import Path
from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from django.conf import settings

from apps.mangas.models.volume import Volume
from apps.mangas.services.volume_processor_service import VolumeFileProcessorService

logger = logging.getLogger(__name__)

# Formatos de arquivo suportados
SUPPORTED_ARCHIVE_FORMATS = ['.zip', '.rar', '.7z', '.pdf']
SUPPORTED_ARCHIVE_MIME_TYPES = [
    'application/zip',
    'application/x-rar-compressed',
    'application/x-7z-compressed',
    'application/x-7z-compressed',
    'application/pdf',
    'application/x-pdf',
    'application/octet-stream'  # Para arquivos sem tipo MIME específico
]

class VolumeForm(forms.ModelForm):
    """Formulário para criação e edição de volumes de mangá."""
    archive_file = forms.FileField(
        label=_('Arquivo com páginas'),
        help_text=_(f'Faça upload de um arquivo compactado contendo as páginas do volume. '
                   f'Formatos suportados: { ", ".join(SUPPORTED_ARCHIVE_FORMATS) }'),
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'accept': ','.join(SUPPORTED_ARCHIVE_FORMATS),
            'class': 'form-control'
        })
    )
    
    class Meta:
        model = Volume
        fields = ['number', 'title', 'cover_image', 'is_published', 'archive_file']
        labels = {
            'number': _('Número do Volume'),
            'title': _('Título (opcional)'),
            'cover_image': _('Capa do Volume (opcional)'),
            'is_published': _('Publicado?'),
            'archive_file': _('Arquivo do Volume'),
        }
        help_texts = {
            'number': _('Número sequencial do volume (ex: 1, 2, 3, etc.)'),
            'title': _('Título opcional para o volume (deixe em branco para usar apenas o número)'),
            'cover_image': _('Imagem de capa do volume (opcional)'),
            'is_published': _('Selecione para tornar este volume visível publicamente'),
            'archive_file': _('Arquivo contendo as páginas do volume (ZIP, RAR, 7Z ou PDF)'),
        }
        widgets = {
            'number': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'cover_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adiciona classes CSS aos campos
        for field_name, field in self.fields.items():
            if field_name != 'is_published':
                field.widget.attrs.update({'class': 'form-control'})
    
    def clean_archive_file(self):
        """Valida o arquivo enviado."""
        archive_file = self.cleaned_data.get('archive_file')
        if not archive_file:
            return None
            
        # Verifica a extensão do arquivo
        file_ext = Path(archive_file.name).suffix.lower()
        if file_ext not in SUPPORTED_ARCHIVE_FORMATS:
            raise forms.ValidationError(
                _('Formato de arquivo não suportado. Formatos aceitos: %(formats)s') % {
                    'formats': ', '.join(SUPPORTED_ARCHIVE_FORMATS)
                }
            )
            
        # Verifica o tamanho máximo do arquivo (200MB)
        max_size = 200 * 1024 * 1024  # 200MB
        if archive_file.size > max_size:
            raise forms.ValidationError(_('O arquivo é muito grande. Tamanho máximo permitido: 200MB'))
            
        # Salva o arquivo temporariamente para validação
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
        try:
            for chunk in archive_file.chunks():
                temp_file.write(chunk)
            temp_file.close()
            
            # Verifica se é um arquivo compactado válido
            if file_ext == '.pdf':
                # Para PDF, verifica se é um PDF válido
                try:
                    import fitz  # PyMuPDF
                    doc = fitz.open(temp_file.name)
                    if not doc.is_pdf:
                        raise forms.ValidationError(_('O arquivo não parece ser um PDF válido.'))
                    doc.close()
                except ImportError:
                    logger.warning("PyMuPDF não está instalado, pulando validação detalhada de PDF")
                except Exception as e:
                    logger.error(f"Erro ao validar PDF: {e}")
                    raise forms.ValidationError(_('O arquivo PDF parece estar corrompido ou não é um PDF válido.'))
            else:
                # Para arquivos compactados, verifica se são válidos
                try:
                    if file_ext == '.zip':
                        import zipfile
                        with zipfile.ZipFile(temp_file.name, 'r') as zf:
                            if not zf.namelist():
                                raise forms.ValidationError(_('O arquivo ZIP está vazio.'))
                    elif file_ext == '.rar':
                        import rarfile
                        with rarfile.RarFile(temp_file.name, 'r') as rf:
                            if not rf.namelist():
                                raise forms.ValidationError(_('O arquivo RAR está vazio.'))
                    elif file_ext == '.7z':
                        import py7zr
                        with py7zr.SevenZipFile(temp_file.name, 'r') as szf:
                            if not szf.getnames():
                                raise forms.ValidationError(_('O arquivo 7Z está vazio.'))
                except ImportError as e:
                    logger.warning(f"Biblioteca não encontrada para validação de {file_ext}: {e}")
                except Exception as e:
                    logger.error(f"Erro ao validar arquivo {file_ext}: {e}")
                    raise forms.ValidationError(_(f'O arquivo {file_ext.upper()} parece estar corrompido ou não é um arquivo compactado válido.'))
            
            # Retorna o arquivo para processamento posterior
            return temp_file.name
            
        except Exception as e:
            # Remove o arquivo temporário em caso de erro
            if os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except Exception as e2:
                    logger.error(f"Erro ao remover arquivo temporário {temp_file.name}: {e2}")
            
            logger.error(f"Erro ao processar arquivo: {e}")
            if not isinstance(e, forms.ValidationError):
                raise forms.ValidationError(_('Ocorreu um erro ao processar o arquivo. Por favor, verifique se o arquivo não está corrompido e tente novamente.'))
            raise
        
    def clean_number(self):
        """Valida se o número do volume é único para o mangá."""
        number = self.cleaned_data.get('number')
        manga = self.instance.manga if hasattr(self.instance, 'manga') else None
        
        if manga and 'manga' in self.data:
            # Verifica se já existe um volume com o mesmo número para este mangá
            queryset = Volume.objects.filter(manga=manga, number=number)
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise forms.ValidationError(
                    _('Já existe um volume com este número para este mangá.')
                )
                
        return number
        
    def save(self, commit=True):
        """
        Sobrescreve o método save para processar o arquivo após salvar o volume.
        """
        # Primeiro, salva o volume
        volume = super().save(commit=commit)
        
        # Se houver um arquivo para processar
        archive_path = self.cleaned_data.get('archive_file')
        if archive_path and os.path.exists(archive_path):
            try:
                # Processa o arquivo
                processor = VolumeFileProcessorService()
                success, message = processor.process_volume_file(volume, archive_path)
                
                if not success:
                    logger.error(f"Erro ao processar arquivo do volume {volume.id}: {message}")
                    # Adiciona a mensagem de erro ao formulário
                    if hasattr(self, '_errors'):
                        self._errors.setdefault('archive_file', []).append(message)
                    elif hasattr(self, 'add_error'):
                        self.add_error('archive_file', message)
                
            except Exception as e:
                logger.exception(f"Erro inesperado ao processar arquivo do volume {volume.id}")
                if hasattr(self, '_errors'):
                    self._errors.setdefault('archive_file', []).append(f"Erro inesperado: {str(e)}")
                elif hasattr(self, 'add_error'):
                    self.add_error('archive_file', f"Erro inesperado: {str(e)}")
            finally:
                # Remove o arquivo temporário
                try:
                    if os.path.exists(archive_path):
                        os.unlink(archive_path)
                except Exception as e:
                    logger.error(f"Erro ao remover arquivo temporário {archive_path}: {e}")
        
        return volume
