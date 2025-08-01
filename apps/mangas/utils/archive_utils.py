import os
import tempfile
import shutil
import zipfile
import rarfile
import py7zr
import tarfile
import patoolib
from pathlib import Path
from typing import List, Tuple, Optional, Generator, Union
from pyunpack import Archive
from PyPDF2 import PdfReader
import logging

logger = logging.getLogger(__name__)

# Formatos suportados
SUPPORTED_ARCHIVE_FORMATS = [
    '.zip', '.rar', '.cbz', '.cbr', '.7z', 
    '.tar', '.tar.gz', '.tar.bz2', '.tar.xz',
    '.cb7', '.cbt', '.cba', '.pdf'
]

# Mapeamento de extensões para tipos de arquivo
ARCHIVE_EXTENSIONS = {
    '.zip': 'zip',
    '.rar': 'rar',
    '.cbz': 'zip',  # CBZ é basicamente um ZIP
    '.cbr': 'rar',  # CBR é basicamente um RAR
    '.7z': '7z',
    '.tar': 'tar',
    '.tar.gz': 'tar',
    '.tgz': 'tar',
    '.tar.bz2': 'tar',
    '.tbz2': 'tar',
    '.tar.xz': 'tar',
    '.txz': 'tar',
    '.cb7': '7z',   # CB7 é basicamente um 7z
    '.cbt': 'tar',  # CBT é basicamente um TAR
    '.cba': 'ace',  # CBA é basicamente um ACE
    '.pdf': 'pdf',
}

class ArchiveHandler:
    """Classe para lidar com vários formatos de arquivos compactados."""
    
    @staticmethod
    def is_archive(file_path: Union[str, os.PathLike]) -> bool:
        """Verifica se o arquivo é um formato suportado."""
        ext = os.path.splitext(str(file_path).lower())[1]
        return ext in SUPPORTED_ARCHIVE_FORMATS
    
    @staticmethod
    def extract_archive(archive_path: Union[str, os.PathLike], 
                       extract_dir: Union[str, os.PathLike] = None) -> str:
        """
        Extrai um arquivo compactado para um diretório temporário.
        
        Args:
            archive_path: Caminho para o arquivo compactado
            extract_dir: Diretório de extração (opcional, usa um diretório temporário se não fornecido)
            
        Returns:
            str: Caminho para o diretório de extração
        """
        archive_path = Path(archive_path)
        if not extract_dir:
            extract_dir = tempfile.mkdtemp(prefix='manga_extract_')
        else:
            os.makedirs(extract_dir, exist_ok=True)
        
        ext = archive_path.suffix.lower()
        
        try:
            if ext == '.pdf':
                # PDFs são tratados de forma diferente
                return str(archive_path)
            
            # Usa pyunpack/patool para extrair o arquivo
            Archive(str(archive_path)).extractall(extract_dir, auto_create_dir=True)
            
            # Se for um TAR dentro de um GZ/BZ2/XZ, precisamos extrair novamente
            for root, _, files in os.walk(extract_dir):
                for file in files:
                    file_path = Path(root) / file
                    if file_path.suffix.lower() in ['.tar', '.tar.gz', '.tgz', '.tar.bz2', '.tbz2', '.tar.xz', '.txz']:
                        with tarfile.open(file_path, 'r:*') as tar:
                            tar.extractall(path=extract_dir)
                        os.remove(file_path)
            
            return str(extract_dir)
            
        except Exception as e:
            logger.error(f"Erro ao extrair arquivo {archive_path}: {e}")
            # Tenta limpar o diretório de extração em caso de erro
            if os.path.exists(extract_dir) and extract_dir.startswith(tempfile.gettempdir()):
                shutil.rmtree(extract_dir, ignore_errors=True)
            raise
    
    @staticmethod
    def list_files(archive_path: Union[str, os.PathLike]) -> List[str]:
        """Lista os arquivos em um arquivo compactado."""
        archive_path = Path(archive_path)
        ext = archive_path.suffix.lower()
        
        if ext == '.pdf':
            return [str(archive_path)]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            extract_dir = ArchiveHandler.extract_archive(archive_path, temp_dir)
            file_list = []
            
            for root, _, files in os.walk(extract_dir):
                for file in files:
                    if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp')):
                        file_list.append(str(Path(root) / file))
            
            return sorted(file_list)
    
    @staticmethod
    def process_archive(archive_path: Union[str, os.PathLike], 
                       callback: callable,
                       **kwargs) -> None:
        """
        Processa um arquivo compactado, extrai e chama uma função de callback para cada arquivo.
        
        Args:
            archive_path: Caminho para o arquivo compactado
            callback: Função a ser chamada para cada arquivo extraído
            **kwargs: Argumentos adicionais para a função de callback
        """
        import fitz  # PyMuPDF
        from io import BytesIO
        
        archive_path = Path(archive_path)
        ext = archive_path.suffix.lower()
        
        if ext == '.pdf':
            # Processa PDFs página por página
            pdf_document = fitz.open(str(archive_path))
            
            for page_num in range(len(pdf_document)):
                # Obtém a página
                page = pdf_document[page_num]
                
                # Renderiza a página como uma imagem (PNG)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # Aumenta a resolução
                
                # Converte para bytes
                img_data = pix.tobytes('png')
                
                # Gera um nome de arquivo único para a página
                page_path = f"{archive_path.stem}_page_{page_num + 1}.png"
                
                # Chama o callback com os dados da imagem
                callback(page_path, img_data, page_number=page_num + 1, **kwargs)
            
            pdf_document.close()
            return
        
        # Para outros formatos, extrai e processa os arquivos
        with tempfile.TemporaryDirectory() as temp_dir:
            extract_dir = ArchiveHandler.extract_archive(archive_path, temp_dir)
            
            # Coleta todos os arquivos de imagem
            image_files = []
            for root, _, files in os.walk(extract_dir):
                for file in files:
                    if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp')):
                        image_files.append(Path(root) / file)
            
            # Ordena os arquivos por nome
            image_files.sort()
            
            # Processa cada arquivo de imagem
            for i, image_path in enumerate(image_files, 1):
                with open(image_path, 'rb') as f:
                    callback(image_path.name, f.read(), page_number=i, **kwargs)
