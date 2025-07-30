"""
Formulário para upload de volumes compactados de mangá.

Este módulo contém o formulário para upload de arquivos compactados contendo
volumes de mangá com múltiplos capítulos organizados em pastas.
"""
import os
from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from ..models.volume import Volume


class VolumeUploadForm(forms.ModelForm):
    """
    Formulário para upload de volume compactado.
    
    Suporta:
    - Um único arquivo compactado (.zip, .rar, .cbz, .cbr, .7z, etc.)
    - Estrutura de pastas: volume_<número>/capitulo_<número>/*.jpg
    """
    # Extensões permitidas para arquivos compactados
    ALLOWED_ARCHIVE_EXTENSIONS = [
        'zip', 'rar', 'cbz', 'cbr', '7z', 'tar', 
        'tar.gz', 'tar.bz2', 'tar.xz', 'cb7', 'cbt', 'cba'
    ]
    
    # Tamanho máximo do arquivo (500MB)
    MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
    
    archive_file = forms.FileField(
        label=_('Arquivo Compactado'),
        help_text=_(f'Arquivo compactado contendo os capítulos do volume. '
                   f'Formatos suportados: {", ".join(ALLOWED_ARCHIVE_EXTENSIONS)}. '
                   f'Tamanho máximo: {MAX_FILE_SIZE/1024/1024:.0f}MB'),
        required=True
    )
    
    class Meta:
        model = Volume
        fields = ['number', 'title', 'cover_image', 'is_published', 'archive_file']
        labels = {
            'number': _('Número do Volume'),
            'title': _('Título (opcional)'),
            'cover_image': _('Capa do Volume (opcional)'),
            'is_published': _('Publicado?'),
        }
        help_texts = {
            'number': _('Número sequencial do volume (ex: 1, 2, 3, etc.)'),
            'title': _('Título opcional para o volume (deixe em branco para usar apenas o número)'),
            'cover_image': _('Imagem de capa do volume (opcional, pode ser extraída do arquivo)'),
            'is_published': _('Selecione para tornar este volume visível publicamente'),
        }
        widgets = {
            'number': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        """Inicializa o formulário com classes CSS e configurações adicionais."""
        super().__init__(*args, **kwargs)
        # Adiciona classes CSS aos campos
        for field_name, field in self.fields.items():
            if field_name != 'is_published':
                field.widget.attrs.update({'class': 'form-control'})
        
        # Torna o campo de arquivo obrigatório apenas na criação
        if self.instance and self.instance.pk:
            self.fields['archive_file'].required = False
    
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
                raise ValidationError(
                    _('Já existe um volume com este número para este mangá.')
                )
        
        return number
    
    def clean_archive_file(self):
        """
        Valida o arquivo compactado enviado.
        """
        archive_file = self.cleaned_data.get('archive_file')
        
        # Se não há arquivo e estamos em uma atualização, retorna o valor atual
        if not archive_file and self.instance and self.instance.pk:
            return None
            
        if not archive_file:
            raise ValidationError(_('É necessário enviar um arquivo compactado.'))
        
        # Obtém a extensão do arquivo
        file_name = archive_file.name.lower()
        ext = os.path.splitext(file_name)[1].lstrip('.')
        
        # Verifica se a extensão é suportada
        if ext not in self.ALLOWED_ARCHIVE_EXTENSIONS:
            raise ValidationError(
                _('Formato de arquivo não suportado. Formatos suportados: %(formats)s') % {
                    'formats': ', '.join(self.ALLOWED_ARCHIVE_EXTENSIONS)
                }
            )
        
        # Verifica o tamanho do arquivo
        if archive_file.size > self.MAX_FILE_SIZE:
            raise ValidationError(
                _('Arquivo muito grande. Tamanho máximo permitido: %(max_size)dMB') % {
                    'max_size': self.MAX_FILE_SIZE // (1024 * 1024)
                }
            )
        
        return archive_file
    
    def save(self, commit=True):
        """
        Salva o volume e processa o arquivo compactado se fornecido.
        """
        # Remove o arquivo do cleaned_data para evitar que o ModelForm tente salvá-lo
        archive_file = self.cleaned_data.pop('archive_file', None)
        
        # Salva o volume
        volume = super().save(commit=commit)
        
        # Se um arquivo foi fornecido, processa-o
        if archive_file and commit:
            from ..services.volume_processor_service import VolumeProcessorService
            
            try:
                processor = VolumeProcessorService()
                success, message = processor.process_volume_archive(volume, archive_file)
                
                if not success:
                    # Se houver erro no processamento, levanta uma exceção
                    raise ValidationError(message)
                
            except Exception as e:
                # Em caso de erro, levanta uma exceção de validação
                raise ValidationError(_(f'Erro ao processar o arquivo: {str(e)}'))
        
        return volume
