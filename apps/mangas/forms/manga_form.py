from django import forms
from apps.mangas.models.manga import Manga
from apps.mangas.models.capitulo import Capitulo
from apps.mangas.models.pagina import Pagina
import zipfile
try:
    import rarfile
except ImportError:
    rarfile = None
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
    - Um único arquivo compactado (.zip, .rar, .cbz, .cbr, .pdf)
    - Múltiplos arquivos de imagem (upload direto de pasta)
    """
    # Extensões permitidas para arquivos compactados
    ALLOWED_ARCHIVE_EXTENSIONS = ['zip', 'rar', 'cbz', 'cbr', '7z', 'tar', 'tar.gz', 'tar.bz2', 'tar.xz', 'cb7', 'cbt', 'cba', 'pdf']
    
    # Tamanho máximo do arquivo (100MB)
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    
    arquivo_capitulo = forms.FileField(
        label='Arquivo do Capítulo',
        help_text='Envie um arquivo compactado (.zip, .rar, .cbz, .cbr, .pdf, etc.) ou uma imagem.',
        required=False
    )
    
    class Meta:
        model = Capitulo
        fields = ['number', 'title', 'arquivo_capitulo']
    
    def clean_arquivo_capitulo(self):
        """
        Valida os arquivos enviados, seja um único arquivo compactado ou múltiplas imagens.
        """
        # Tenta obter o arquivo de diferentes formas
        arquivo = None
        
        # Primeiro, tenta obter como arquivo único
        if 'arquivo_capitulo' in self.files:
            arquivo = self.files['arquivo_capitulo']
        
        # Se não encontrou, tenta obter da lista
        if not arquivo and 'arquivo_capitulo' in self.files:
            arquivos = self.files.getlist('arquivo_capitulo')
            if arquivos:
                arquivo = arquivos[0]
        
        # Se não há arquivo, retorna None
        if not arquivo:
            return None
        
        # Valida o arquivo
        nome_arquivo = getattr(arquivo, 'name', '')
        ext = os.path.splitext(nome_arquivo)[1].lower().lstrip('.')
        
        # Verifica se a extensão é suportada
        if ext not in self.ALLOWED_ARCHIVE_EXTENSIONS + ['jpg', 'jpeg', 'png', 'webp', 'gif', 'bmp', 'tiff', 'tif']:
            raise forms.ValidationError(
                f'Formato de arquivo não suportado: {nome_arquivo}. ' \
                f'Formatos suportados: {", ".join(self.ALLOWED_ARCHIVE_EXTENSIONS + ["jpg", "jpeg", "png", "webp", "gif", "bmp", "tiff", "tif"])}'
            )
        
        # Verifica o tamanho do arquivo
        if ext in self.ALLOWED_ARCHIVE_EXTENSIONS:
            # Para arquivos compactados, usa o limite maior
            if arquivo.size > self.MAX_FILE_SIZE:
                raise forms.ValidationError(f'Arquivo muito grande. Tamanho máximo permitido: {self.MAX_FILE_SIZE/1024/1024:.0f}MB')
        else:
            # Para imagens, usa o limite menor
            if arquivo.size > 10 * 1024 * 1024:  # 10MB
                raise forms.ValidationError(f'Arquivo muito grande. Tamanho máximo permitido: 10MB')
        
        return arquivo

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