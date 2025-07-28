from django import forms
from django.core.validators import FileExtensionValidator
from django.core.files.uploadedfile import UploadedFile
from apps.mangas.models.manga import Manga
from apps.mangas.models.capitulo import Capitulo
from apps.mangas.models.pagina import Pagina
from apps.mangas.widgets import MultipleFileInput
import zipfile
import rarfile
import os
from typing import List, Union, Optional

class MangaForm(forms.ModelForm):
    class Meta:
        model = Manga
        fields = ['title', 'author', 'description', 'cover_image']

class CapituloForm(forms.ModelForm):
    class Meta:
        model = Capitulo
        fields = ['number', 'title']

class CapituloCompleteForm(forms.ModelForm):
    """
    Formulário para upload de capítulo completo.
    Suporta:
    - Um único arquivo compactado (.zip, .rar, .cbz, .cbr)
    - Múltiplos arquivos de imagem (upload direto de pasta)
    """
    # Extensões permitidas para arquivos compactados
    ALLOWED_ARCHIVE_EXTENSIONS = ['zip', 'rar', 'cbz', 'cbr', '7z', 'tar', 'tar.gz', 'tar.bz2', 'tar.xz', 'cb7', 'cbt', 'cba']
    
    # Tamanho máximo do arquivo (100MB)
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    
    arquivo_capitulo = forms.FileField(
        label='Arquivo do Capítulo',
        help_text='Envie um arquivo compactado (.zip, .rar, .cbz, .cbr, etc.) ou selecione uma pasta com imagens. Você pode selecionar múltiplos arquivos ou uma pasta inteira.',
        required=False,
        widget=MultipleFileInput(),
        validators=[
            FileExtensionValidator(
                allowed_extensions=ALLOWED_ARCHIVE_EXTENSIONS + ['jpg', 'jpeg', 'png', 'webp', 'gif', 'bmp', 'tiff', 'tif']
            )
        ]
    )
    
    class Meta:
        model = Capitulo
        fields = ['number', 'title', 'arquivo_capitulo']
    
    def clean_arquivo_capitulo(self):
        """
        Valida os arquivos enviados, seja um único arquivo compactado ou múltiplas imagens.
        """
        arquivos = self.files.getlist('arquivo_capitulo') if 'arquivo_capitulo' in self.files else []
        
        # Se não há arquivos, retorna None
        if not arquivos:
            return None
        
        # Se for um único arquivo, verifica se é um arquivo compactado
        if len(arquivos) == 1:
            arquivo = arquivos[0]
            nome_arquivo = getattr(arquivo, 'name', '')
            ext = os.path.splitext(nome_arquivo)[1].lower().lstrip('.')
            
            # Se for um arquivo compactado, valida o tamanho máximo
            if ext in self.ALLOWED_ARCHIVE_EXTENSIONS:
                if arquivo.size > self.MAX_FILE_SIZE:
                    raise forms.ValidationError(f'Arquivo muito grande. Tamanho máximo permitido: {self.MAX_FILE_SIZE/1024/1024:.0f}MB')
                return arquivo
            
            # Se for uma imagem, continua para validar como múltiplos arquivos
            return arquivos
        
        # Se são múltiplos arquivos, valida cada um
        for arquivo in arquivos:
            # Obtém o nome e extensão do arquivo
            nome_arquivo = getattr(arquivo, 'name', '')
            ext = os.path.splitext(nome_arquivo)[1].lower().lstrip('.')
            
            # Verifica se é uma imagem
            if ext not in ['jpg', 'jpeg', 'png', 'webp', 'gif', 'bmp', 'tiff', 'tif']:
                raise forms.ValidationError(
                    f'Formato de arquivo não suportado: {nome_arquivo}. ' \
                    'Use apenas imagens (JPG, PNG, WebP, GIF, BMP, TIFF).'
                )
            
            # Verifica o tamanho do arquivo (máx 10MB por imagem)
            if arquivo.size > 10 * 1024 * 1024:  # 10MB
                raise forms.ValidationError(
                    f'Arquivo muito grande: {nome_arquivo} ' \
                    f'({arquivo.size/1024/1024:.1f}MB). ' \
                    'Tamanho máximo permitido: 10MB por arquivo.'
                )
        
        return arquivos

class PaginaForm(forms.ModelForm):
    class Meta:
        model = Pagina
        fields = ['number', 'image']

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            ext = image.name.lower().split('.')[-1]
            if ext not in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
                raise forms.ValidationError('Apenas imagens JPG, PNG, WEBP ou GIF são permitidas.')
            if image.size > 10 * 1024 * 1024:
                raise forms.ValidationError('Imagem muito grande (máx. 10MB).')
        return image