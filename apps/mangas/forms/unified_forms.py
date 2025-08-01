from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.forms.widgets import ClearableFileInput
from typing import List, Optional

from apps.mangas.models import Manga, Volume, Capitulo, Pagina
from apps.mangas.validators import (
    ImageFileValidator,
    ArchiveFileValidator,
    ContentValidator
)
from apps.mangas.constants.file_limits import (
    MAX_UPLOAD_SIZE,
    ALLOWED_IMAGE_EXTENSIONS,
    ALLOWED_ARCHIVE_EXTENSIONS,
    MIN_IMAGE_WIDTH,
    MIN_IMAGE_HEIGHT,
    MAX_IMAGE_WIDTH,
    MAX_IMAGE_HEIGHT,
    ERROR_MESSAGES,
    get_allowed_image_extensions_str,
    get_allowed_archive_extensions_str,
    get_max_upload_size_mb
)


class CustomFileInput(ClearableFileInput):
    """Widget customizado para upload de arquivos com informações de validação."""
    
    def __init__(self, attrs=None, allowed_extensions=None, max_size_mb=None):
        super().__init__(attrs)
        self.allowed_extensions = allowed_extensions or []
        self.max_size_mb = max_size_mb
    
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['allowed_extensions'] = self.allowed_extensions
        context['widget']['max_size_mb'] = self.max_size_mb
        return context


class UnifiedMangaForm(forms.ModelForm):
    """Formulário unificado para criação e edição de mangás."""
    
    cover_image = forms.ImageField(
        label=_('Imagem de Capa'),
        required=False,
        validators=[
            ImageFileValidator(
                min_width=MIN_IMAGE_WIDTH,
                min_height=MIN_IMAGE_HEIGHT,
                max_width=MAX_IMAGE_WIDTH,
                max_height=MAX_IMAGE_HEIGHT
            )
        ],
        widget=CustomFileInput(
            attrs={
                'accept': 'image/*',
                'class': 'form-control-file'
            },
            allowed_extensions=ALLOWED_IMAGE_EXTENSIONS,
            max_size_mb=get_max_upload_size_mb()
        ),
        help_text=_(
            f'Formatos aceitos: {get_allowed_image_extensions_str()}. '
            f'Tamanho máximo: {get_max_upload_size_mb()}MB. '
            f'Dimensões: {MIN_IMAGE_WIDTH}x{MIN_IMAGE_HEIGHT} até {MAX_IMAGE_WIDTH}x{MAX_IMAGE_HEIGHT}px.'
        )
    )
    
    class Meta:
        model = Manga
        fields = ['title', 'author', 'description', 'cover_image']  # Removidos 'status' e 'genre'
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Digite o título do mangá')
            }),
            'author': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Nome do autor')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('Descrição do mangá')
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adicionar validador de conteúdo único para título
        if not self.instance.pk:  # Apenas para novos mangás
            self.fields['title'].validators.append(
                ContentValidator(field_name='title', model=Manga)
            )
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if title:
            title = title.strip()
        return title
    
    def save(self, commit=True):
        manga = super().save(commit=False)
        if commit:
            manga.save()
        return manga


class UnifiedVolumeForm(forms.ModelForm):
    """Formulário unificado para criação e edição de volumes."""
    
    class Meta:
        model = Volume
        fields = ['number', 'title']  # Removido 'description'
        widgets = {
            'number': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': _('Número do volume')
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Título do volume (opcional)')
            })
        }
    
    def __init__(self, manga=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.manga = manga
        
        # Validação de número único por mangá
        if not self.instance.pk and manga:
            self.fields['number'].validators.append(
                ContentValidator(
                    field_name='number', 
                    model=Volume,
                    filter_kwargs={'manga': manga}
                )
            )
    
    def save(self, commit=True):
        volume = super().save(commit=False)
        if self.manga:
            volume.manga = self.manga
        if commit:
            volume.save()
        return volume


class UnifiedCapituloForm(forms.ModelForm):
    """Formulário unificado para criação e edição de capítulos."""
    
    class Meta:
        model = Capitulo
        fields = ['number', 'title']  # Removido 'description'
        widgets = {
            'number': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'step': 0.1,
                'placeholder': _('Número do capítulo')
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Título do capítulo (opcional)')
            })
        }
    
    def __init__(self, manga=None, volume=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.manga = manga
        self.volume = volume
        
        # Validação de número único por volume
        if not self.instance.pk and volume:
            self.fields['number'].validators.append(
                ContentValidator(
                    field_name='number', 
                    model=Capitulo,
                    filter_kwargs={'volume': volume}
                )
            )
    
    def save(self, commit=True):
        capitulo = super().save(commit=False)
        if self.volume:
            capitulo.volume = self.volume
        if commit:
            capitulo.save()
        return capitulo


class UnifiedCapituloCompleteForm(UnifiedCapituloForm):
    """Formulário para upload completo de capítulo com arquivo."""
    
    arquivo_capitulo = forms.FileField(
        label=_('Arquivo do Capítulo'),
        required=True,
        validators=[ArchiveFileValidator()],
        widget=CustomFileInput(
            attrs={
                'accept': '.zip,.rar,.cbz,.cbr,.7z,.pdf',
                'class': 'form-control-file'
            },
            allowed_extensions=ALLOWED_ARCHIVE_EXTENSIONS,
            max_size_mb=get_max_upload_size_mb()
        ),
        help_text=_(
            f'Formatos aceitos: {get_allowed_archive_extensions_str()}. '
            f'Tamanho máximo: {get_max_upload_size_mb()}MB.'
        )
    )
    
    class Meta(UnifiedCapituloForm.Meta):
        fields = UnifiedCapituloForm.Meta.fields + ['arquivo_capitulo']
    
    def clean_arquivo_capitulo(self):
        arquivo = self.cleaned_data.get('arquivo_capitulo')
        if arquivo:
            # Validação adicional se necessário
            pass
        return arquivo
    
    def save(self, commit=True):
        capitulo = super().save(commit)
        # Aqui você pode processar o arquivo se necessário
        # arquivo = self.cleaned_data.get('arquivo_capitulo')
        return capitulo


class UnifiedPaginaForm(forms.ModelForm):
    """Formulário unificado para criação e edição de páginas."""
    
    image = forms.ImageField(
        label=_('Imagem da Página'),
        validators=[
            ImageFileValidator(
                min_width=MIN_IMAGE_WIDTH,
                min_height=MIN_IMAGE_HEIGHT,
                max_width=MAX_IMAGE_WIDTH,
                max_height=MAX_IMAGE_HEIGHT
            )
        ],
        widget=CustomFileInput(
            attrs={
                'accept': 'image/*',
                'class': 'form-control-file'
            },
            allowed_extensions=ALLOWED_IMAGE_EXTENSIONS,
            max_size_mb=get_max_upload_size_mb()
        ),
        help_text=_(
            f'Formatos aceitos: {get_allowed_image_extensions_str()}. '
            f'Tamanho máximo: {get_max_upload_size_mb()}MB. '
            f'Dimensões: {MIN_IMAGE_WIDTH}x{MIN_IMAGE_HEIGHT} até {MAX_IMAGE_WIDTH}x{MAX_IMAGE_HEIGHT}px.'
        )
    )
    
    class Meta:
        model = Pagina
        fields = ['number', 'image']
        widgets = {
            'number': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': _('Número da página')
            })
        }
    
    def __init__(self, capitulo=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.capitulo = capitulo
        
        # Validação de número único por capítulo
        if not self.instance.pk and capitulo:
            self.fields['number'].validators.append(
                ContentValidator(
                    field_name='number', 
                    model=Pagina,
                    filter_kwargs={'capitulo': capitulo}
                )
            )
    
    def save(self, commit=True):
        pagina = super().save(commit=False)
        if self.capitulo:
            pagina.capitulo = self.capitulo
        if commit:
            pagina.save()
        return pagina


# Adicionar no final do arquivo
class MultipleFileInput(forms.ClearableFileInput):
    """Widget para upload de múltiplos arquivos."""
    allow_multiple_selected = True

class UnifiedBulkUploadForm(forms.Form):
    """Formulário para upload em lote de páginas."""
    
    files = forms.FileField(
        widget=MultipleFileInput(attrs={
            'multiple': True,
            'accept': 'image/*',
            'class': 'form-control-file'
        }),
        label=_('Arquivos de Imagem'),
        help_text=_('Selecione múltiplas imagens para upload em lote.')
    )
    
    def clean_files(self):
        files = self.files.getlist('files')
        if not files:
            raise ValidationError("Pelo menos um arquivo deve ser selecionado.")
        
        for file in files:
            # Validar cada arquivo individualmente
            validator = ImageFileValidator()
            validator(file)
        
        return files