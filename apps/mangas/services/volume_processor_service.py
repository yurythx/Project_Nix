
"""Serviço para processamento de arquivos de volumes de mangá.

Este módulo contém a implementação concreta do serviço de processamento de arquivos
que extrai páginas de imagens de vários formatos de arquivo compactado para volumes.
"""
from io import BytesIO
import os
import zipfile
try:
    import rarfile
except ImportError:
    rarfile = None
try:
    import tarfile
except ImportError:
    tarfile = None
try:
    import py7zr
except ImportError:
    py7zr = None
try:
    import PyPDF2
    import fitz  # PyMuPDF
except ImportError:
    PyPDF2 = None
    fitz = None
import tempfile
import shutil
from pathlib import Path
from typing import List, Tuple, Optional, BinaryIO, Union, Dict, Any
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from PIL import Image, UnidentifiedImageError, ImageFile
import logging
import re

from ..models.volume import Volume
from ..models.capitulo import Capitulo
from ..models.pagina import Pagina

# Configura o Pillow para processar imagens grandes
ImageFile.LOAD_TRUNCATED_IMAGES = True

logger = logging.getLogger(__name__)

class VolumeFileProcessorService:
    """
    Implementação concreta do serviço de processamento de arquivos de volumes de mangá.
    
    Esta classe é responsável por processar arquivos de volumes de mangá em formatos
    compactados (.zip, .rar, .7z, .pdf) e extrair as páginas de imagem contidas neles.
    """
    # Formatos de arquivo suportados
    SUPPORTED_FORMATS = ['.zip', '.rar', '.7z', '.pdf']
    
    # Extensões de imagem suportadas
    IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp']
    
    # Arquivos a serem ignorados
    IGNORED_FILES = ['.DS_Store', 'Thumbs.db', 'desktop.ini', '.txt', '.pdf']
    
    # Tamanho máximo do arquivo (200MB para arquivos compactados)
    MAX_ARCHIVE_SIZE = 200 * 1024 * 1024  # 200MB
    MAX_IMAGE_SIZE = 20 * 1024 * 1024      # 20MB
    
    # Número mínimo e máximo de páginas por volume
    MIN_PAGES = 1
    MAX_PAGES = 1000
    
    def __init__(self):
        """Inicializa o serviço com um diretório temporário vazio."""
        self.temp_dir = None
    
    def process_volume_file(self, volume: Volume, file_path: str) -> Tuple[bool, str]:
        """
        Processa um arquivo de volume e cria as páginas correspondentes.
        
        Args:
            volume: Instância do modelo Volume
            file_path: Caminho para o arquivo a ser processado
            
        Returns:
            Tupla (success, message) indicando o resultado da operação
        """
        if not isinstance(volume, Volume) or not volume.pk:
            raise ValueError("O parâmetro 'volume' deve ser uma instância de Volume válida")
        
        # Verifica se o arquivo existe
        if not os.path.exists(file_path):
            return False, f"Arquivo não encontrado: {file_path}"
        
        # Obtém a extensão do arquivo
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Verifica se o formato é suportado
        if file_ext not in self.SUPPORTED_FORMATS:
            return False, f"Formato de arquivo não suportado: {file_ext}"
        
        try:
            # Cria um diretório temporário
            self.temp_dir = tempfile.mkdtemp(prefix='manga_volume_')
            
            # Processa o arquivo de acordo com sua extensão
            if file_ext == '.pdf':
                success, message = self._process_pdf(volume, file_path)
            else:
                success, message = self._process_archive(volume, file_path, file_ext)
            
            # Se o processamento foi bem-sucedido, marca o volume como extraído
            if success:
                volume.extracted = True
                volume.save(update_fields=['extracted'])
            
            return success, message
            
        except Exception as e:
            logger.exception(f"Erro ao processar arquivo do volume {volume.id}")
            return False, f"Erro ao processar arquivo: {str(e)}"
            
        finally:
            # Remove o diretório temporário
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
    
    def _process_archive(self, volume: Volume, file_path: str, file_ext: str) -> Tuple[bool, str]:
        """
        Processa um arquivo compactado (ZIP, RAR, 7Z).
        
        Args:
            volume: Instância do modelo Volume
            file_path: Caminho para o arquivo compactado
            file_ext: Extensão do arquivo (.zip, .rar, .7z)
            
        Returns:
            Tupla (success, message)
        """
        try:
            # Extrai o arquivo compactado
            if file_ext == '.zip':
                self._extract_zip(file_path)
            elif file_ext == '.rar' and rarfile:
                self._extract_rar(file_path)
            elif file_ext == '.7z' and py7zr:
                self._extract_7z(file_path)
            else:
                return False, f"Formato não suportado ou biblioteca não instalada: {file_ext}"
            
            # Processa as imagens extraídas
            return self._process_extracted_images(volume)
            
        except Exception as e:
            logger.exception(f"Erro ao processar arquivo compactado: {file_path}")
            return False, f"Erro ao processar arquivo compactado: {str(e)}"
    
    def _process_pdf(self, volume: Volume, file_path: str) -> Tuple[bool, str]:
        """
        Processa um arquivo PDF, convertendo cada página em uma imagem.
        
        Args:
            volume: Instância do modelo Volume
            file_path: Caminho para o arquivo PDF
            
        Returns:
            Tupla (success, message)
        """
        try:
            if not fitz:
                return False, "A biblioteca PyMuPDF (fitz) não está instalada. Instale com 'pip install pymupdf'"
            
            # Cria um diretório para as imagens do PDF
            pdf_images_dir = os.path.join(self.temp_dir, 'pdf_images')
            os.makedirs(pdf_images_dir, exist_ok=True)
            
            # Abre o PDF
            doc = fitz.open(file_path)
            
            # Converte cada página em imagem
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap()
                
                # Salva a imagem
                img_path = os.path.join(pdf_images_dir, f"page_{page_num + 1:03d}.png")
                pix.save(img_path)
            
            # Processa as imagens extraídas
            return self._process_extracted_images(volume, pdf_images_dir)
            
        except Exception as e:
            logger.exception(f"Erro ao processar PDF: {file_path}")
            return False, f"Erro ao processar PDF: {str(e)}"
    
    def _extract_zip(self, file_path: str) -> None:
        """Extrai um arquivo ZIP."""
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(self.temp_dir)
    
    def _extract_rar(self, file_path: str) -> None:
        """Extrai um arquivo RAR."""
        if not rarfile:
            raise ImportError("A biblioteca rarfile não está instalada. Instale com 'pip install rarfile'")
        with rarfile.RarFile(file_path, 'r') as rar_ref:
            rar_ref.extractall(self.temp_dir)
    
    def _extract_7z(self, file_path: str) -> None:
        """Extrai um arquivo 7Z."""
        if not py7zr:
            raise ImportError("A biblioteca py7zr não está instalada. Instale com 'pip install py7zr'")
        with py7zr.SevenZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(self.temp_dir)
    
    def _process_extracted_images(self, volume: Volume, base_dir: str = None) -> Tuple[bool, str]:
        """
        Processa as imagens extraídas e cria as páginas no banco de dados.
        
        Args:
            volume: Instância do modelo Volume
            base_dir: Diretório base para procurar imagens (opcional, usa self.temp_dir se None)
            
        Returns:
            Tupla (success, message)
        """
        if base_dir is None:
            base_dir = self.temp_dir
        
        # Encontra todos os arquivos de imagem
        image_files = []
        for root, _, files in os.walk(base_dir):
            for file in files:
                file_ext = os.path.splitext(file)[1].lower()
                if file_ext in self.IMAGE_EXTENSIONS and not any(ignored in file for ignored in self.IGNORED_FILES):
                    image_files.append(os.path.join(root, file))
        
        # Ordena os arquivos pelo nome
        image_files.sort(key=lambda x: [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', x)])
        
        # Verifica o número de páginas
        if len(image_files) < self.MIN_PAGES:
            return False, f"O volume deve ter pelo menos {self.MIN_PAGES} páginas"
        if len(image_files) > self.MAX_PAGES:
            return False, f"O volume não pode ter mais de {self.MAX_PAGES} páginas"
        
        try:
            # Cria um capítulo para o volume
            capitulo = Capitulo.objects.create(
                volume=volume,
                number=1,  # Capítulo 1 para o volume
                title=f"Volume {volume.number}",
                is_published=volume.is_published
            )
            
            # Diretório de destino para as imagens
            pages_dir = os.path.join('pages', str(volume.id))
            os.makedirs(os.path.join('media', pages_dir), exist_ok=True)
            
            # Processa cada imagem
            for i, img_path in enumerate(image_files, start=1):
                # Gera um nome único para o arquivo
                filename = f"page_{i:03d}{os.path.splitext(img_path)[1]}"
                dest_path = os.path.join(pages_dir, filename)
                
                # Abre e verifica a imagem
                try:
                    with Image.open(img_path) as img:
                        # Salva a imagem no diretório de mídia
                        img.save(os.path.join('media', dest_path), quality=85, optimize=True)
                        
                        # Cria o registro da página no banco de dados
                        Pagina.objects.create(
                            capitulo=capitulo,
                            number=i,
                            image=dest_path,
                            width=img.width,
                            height=img.height,
                            file_size=os.path.getsize(os.path.join('media', dest_path))
                        )
                        
                except (UnidentifiedImageError, OSError) as e:
                    logger.warning(f"Não foi possível processar a imagem {img_path}: {str(e)}")
                    continue
            
            return True, f"Volume processado com sucesso. {len(image_files)} páginas adicionadas."
            
        except Exception as e:
            logger.exception("Erro ao processar imagens extraídas")
            return False, f"Erro ao processar imagens: {str(e)}"
