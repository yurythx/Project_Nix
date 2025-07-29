"""
Serviço para processamento de arquivos de capítulos de mangá.

Este módulo contém a implementação concreta do serviço de processamento de arquivos
que extrai páginas de imagens de vários formatos de arquivo compactado.
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
from typing import List, Tuple, Optional, BinaryIO, Union
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from PIL import Image, UnidentifiedImageError, ImageFile
import logging

from ..constants import (
    ALLOWED_IMAGE_EXTENSIONS, ALLOWED_ARCHIVE_EXTENSIONS, MAX_IMAGE_SIZE, MAX_ARCHIVE_SIZE, MAX_PAGES_PER_CHAPTER, MESSAGES
)
from ..interfaces.file_processor_interface import IFileProcessorService
from ..models.capitulo import Capitulo
from ..models.pagina import Pagina

# Configura o Pillow para processar imagens grandes
ImageFile.LOAD_TRUNCATED_IMAGES = True

logger = logging.getLogger(__name__)


class MangaFileProcessorService(IFileProcessorService):
    """
    Implementação concreta do serviço de processamento de arquivos de mangá.
    
    Esta classe é responsável por processar arquivos de capítulos de mangá em formatos
    compactados (.zip, .rar, .cbz, .cbr) e extrair as páginas de imagem contidas neles.
    """
    # Formatos de arquivo suportados
    SUPPORTED_FORMATS = [
        '.zip', '.rar', '.cbz', '.cbr', '.7z', '.tar', 
        '.tar.gz', '.tgz', '.tar.bz2', '.tbz2', '.tar.xz', 
        '.txz', '.cb7', '.cbt', '.cba', '.pdf'
    ]
    
    # Extensões de imagem suportadas
    IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.tiff', '.tif']
    
    # Tamanho máximo do arquivo (100MB para arquivos compactados, 10MB para imagens individuais)
    MAX_ARCHIVE_SIZE = 100 * 1024 * 1024  # 100MB
    MAX_IMAGE_SIZE = 10 * 1024 * 1024      # 10MB
    
    def __init__(self):
        """Inicializa o serviço com um diretório temporário vazio."""
        self.temp_dir = None
    
    def process_chapter_file(self, chapter: Capitulo, file: BinaryIO) -> Tuple[bool, str]:
        """
        Processa um arquivo de capítulo e cria as páginas correspondentes.
        
        Este método é responsável por validar o arquivo, extrair as imagens e criar
        as páginas do capítulo no banco de dados. Pode receber tanto um arquivo compactado
        quanto um arquivo ZIP temporário criado a partir de uma pasta.
        
        Args:
            chapter: Instância do modelo Capitulo
            file: Arquivo a ser processado (pode ser .zip, .rar, etc.) ou arquivo temporário
            
        Returns:
            Tupla (success, message) indicando o resultado da operação
            
        Raises:
            ValueError: Se o parâmetro chapter não for uma instância de Capitulo válida
            ValueError: Se o arquivo não for de um formato suportado
        """
        if not isinstance(chapter, Capitulo) or not chapter.pk:
            raise ValueError("O parâmetro 'chapter' deve ser uma instância de Capitulo válida")
            
        # Verifica se o arquivo é um arquivo temporário de pasta
        is_temp_zip = hasattr(file, 'name') and file.name == 'capitulo_temp.zip'
        
        # Valida o formato do arquivo, a menos que seja um arquivo temporário
        if not is_temp_zip:
            file_extension = os.path.splitext(file.name)[1].lower()
            if file_extension not in self.SUPPORTED_FORMATS:
                from ..constants import MESSAGES
                raise ValueError(
                    MESSAGES['invalid_archive'].format(
                        ', '.join(self.SUPPORTED_FORMATS)
                    )
                )
            
            # Verifica o tamanho do arquivo
            if hasattr(file, 'size'):
                max_size = self.MAX_ARCHIVE_SIZE if file_extension in self.SUPPORTED_FORMATS else self.MAX_IMAGE_SIZE
                if file.size > max_size:
                    max_size_mb = max_size / (1024 * 1024)
                    raise ValueError(
                        f"O arquivo é muito grande. "
                        f"Tamanho máximo permitido: {max_size_mb:.1f}MB"
                    )
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                self.temp_dir = temp_dir
                logger.info(f"Iniciando processamento do arquivo: {file.name if hasattr(file, 'name') else 'arquivo sem nome'}")
                
                image_files, filter_errors = self._extract_images(file, file_extension if not is_temp_zip else '.zip', collect_errors=True)
                logger.info(f"Imagens extraídas: {len(image_files)} arquivos encontrados")
                
                # Validação do limite de páginas
                if len(image_files) > MAX_PAGES_PER_CHAPTER:
                    return False, f"O capítulo excede o limite de {MAX_PAGES_PER_CHAPTER} páginas. Foram encontradas {len(image_files)} imagens válidas. Reduza a quantidade e tente novamente."
                if not image_files:
                    logger.error(f"Nenhuma imagem encontrada. Erros: {filter_errors}")
                    return False, "Nenhuma imagem válida encontrada no arquivo ou pasta.\n" + ("\n".join(filter_errors) if filter_errors else "")
                
                logger.info(f"Criando {len(image_files)} páginas para o capítulo {chapter.id}")
                create_errors = self._create_pages(chapter, image_files, collect_errors=True)
                total_criadas = len(image_files) - len(create_errors)
                
                if total_criadas == 0:
                    logger.error(f"Nenhuma página criada. Erros: {create_errors}")
                    chapter.delete()
                    return False, "Nenhuma página foi criada com sucesso. O capítulo foi removido.\n" + ("\n".join(filter_errors + create_errors) if (filter_errors or create_errors) else "")
                
                msg = f"Capítulo processado com sucesso. {total_criadas} páginas criadas a partir do {'arquivo' if not is_temp_zip else 'conteúdo da pasta'}."
                if filter_errors or create_errors:
                    msg += "\n\nAvisos/erros:\n" + "\n".join(filter_errors + create_errors)
                
                logger.info(f"Upload de capítulo processado com sucesso: {total_criadas} páginas criadas.")
                return True, msg
        except Exception as e:
            logger.error(f"Erro ao processar arquivo do capítulo: {str(e)}", exc_info=True)
            return False, f"Erro ao processar arquivo: {str(e)}"
        finally:
            self.temp_dir = None
    
    def _extract_file(self, file: BinaryIO, file_extension: str) -> str:
        """
        Extrai o conteúdo de um arquivo compactado para um diretório temporário.
        """
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)
            file.seek(0)  # Garante leitura do início
            for chunk in file.chunks():
                temp_file.write(chunk)
            temp_file.close()
            extract_dir = os.path.join(tempfile.gettempdir(), f'manga_extract_{os.urandom(8).hex()}')
            os.makedirs(extract_dir, exist_ok=True)
            try:
                # ZIP e CBZ
                if file_extension in ['.zip', '.cbz']:
                    with zipfile.ZipFile(temp_file.name, 'r') as zip_ref:
                        zip_ref.extractall(extract_dir)
                # RAR e CBR
                elif file_extension in ['.rar', '.cbr'] and rarfile:
                    with rarfile.RarFile(temp_file.name, 'r') as rar_ref:
                        rar_ref.extractall(extract_dir)
                # 7Z e CB7
                elif file_extension in ['.7z', '.cb7'] and py7zr:
                    with py7zr.SevenZipFile(temp_file.name, mode='r') as sz_ref:
                        sz_ref.extractall(extract_dir)
                # TAR e derivados
                elif file_extension in ['.tar', '.cbt', '.cba'] or file_extension.startswith('.tar.'):
                    mode = 'r'
                    if file_extension.endswith('.gz') or file_extension.endswith('.tgz'):
                        mode += ':gz'
                    elif file_extension.endswith('.bz2') or file_extension.endswith('.tbz2'):
                        mode += ':bz2'
                    elif file_extension.endswith('.xz') or file_extension.endswith('.txz'):
                        mode += ':xz'
                    with tarfile.open(temp_file.name, mode) as tar_ref:
                        tar_ref.extractall(extract_dir)
                else:
                    raise ValueError(f"Formato de arquivo não suportado: {file_extension}")
                logger.info(f"Arquivo compactado extraído com sucesso: {file_extension}")
                return extract_dir
            except Exception as extract_error:
                if 'password required' in str(extract_error).lower():
                    raise RuntimeError("Arquivo protegido por senha não é suportado")
                elif 'not a zip file' in str(extract_error).lower():
                    raise RuntimeError("Arquivo corrompido ou em formato inválido")
                elif 'bad magic number' in str(extract_error).lower():
                    raise RuntimeError("Formato de arquivo inválido ou corrompido")
                else:
                    raise extract_error
        except Exception as e:
            logger.error(f"Erro ao extrair arquivo {file_extension}: {str(e)}", exc_info=True)
            if 'extract_dir' in locals() and os.path.exists(extract_dir):
                shutil.rmtree(extract_dir, ignore_errors=True)
            if 'No such file or directory' in str(e):
                raise RuntimeError("Arquivo não encontrado ou inacessível")
            elif 'Invalid data' in str(e):
                raise RuntimeError("Dados inválidos no arquivo")
            else:
                raise RuntimeError(f"Erro ao processar o arquivo: {str(e)}")
        finally:
            if 'temp_file' in locals() and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except Exception as e:
                    logger.warning(f"Não foi possível remover arquivo temporário {temp_file.name}: {str(e)}")

    def _extract_pdf_pages(self, file: BinaryIO) -> List[str]:
        """
        Extrai páginas de um arquivo PDF e as converte em imagens.
        
        Args:
            file: Arquivo PDF
            
        Returns:
            Lista de caminhos para as imagens das páginas extraídas
            
        Raises:
            ValueError: Se o PDF não puder ser processado
        """
        if not PyPDF2 or not fitz:
            raise ValueError("Bibliotecas PyPDF2 e PyMuPDF são necessárias para processar PDFs")
        
        try:
            # Salva o PDF temporariamente
            temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            file.seek(0)
            for chunk in file.chunks():
                temp_pdf.write(chunk)
            temp_pdf.close()
            
            # Cria diretório temporário para as imagens
            extract_dir = os.path.join(tempfile.gettempdir(), f'pdf_extract_{os.urandom(8).hex()}')
            os.makedirs(extract_dir, exist_ok=True)
            
            try:
                # Abre o PDF com PyMuPDF
                pdf_document = fitz.open(temp_pdf.name)
                
                # Lista para armazenar os caminhos das imagens
                image_files = []
                
                # Converte cada página para imagem
                for page_num in range(len(pdf_document)):
                    page = pdf_document.load_page(page_num)
                    
                    # Define a matriz de transformação para DPI 150
                    mat = fitz.Matrix(150/72, 150/72)  # 72 DPI é o padrão do PDF
                    
                    # Renderiza a página como imagem
                    pix = page.get_pixmap(matrix=mat)
                    
                    # Salva a imagem
                    image_path = os.path.join(extract_dir, f'page_{page_num+1:03d}.png')
                    pix.save(image_path)
                    
                    image_files.append(image_path)
                
                # Fecha o documento
                pdf_document.close()
                
                logger.info(f"PDF processado com sucesso: {len(image_files)} páginas extraídas")
                return image_files
                
            except Exception as e:
                if 'extract_dir' in locals() and os.path.exists(extract_dir):
                    shutil.rmtree(extract_dir, ignore_errors=True)
                raise e
                
        except Exception as e:
            logger.error(f"Erro ao processar PDF: {str(e)}", exc_info=True)
            if 'password required' in str(e).lower():
                raise ValueError("PDF protegido por senha não é suportado")
            elif 'not a pdf' in str(e).lower():
                raise ValueError("Arquivo não é um PDF válido")
            else:
                raise ValueError(f"Erro ao processar PDF: {str(e)}")
        finally:
            if 'temp_pdf' in locals() and os.path.exists(temp_pdf.name):
                try:
                    os.unlink(temp_pdf.name)
                except Exception as e:
                    logger.warning(f"Não foi possível remover PDF temporário {temp_pdf.name}: {str(e)}")

    def _extract_images(self, file: BinaryIO, file_extension: str, collect_errors=False) -> Union[List[str], Tuple[List[str], list]]:
        """
        Extrai imagens de um arquivo compactado ou PDF.
        
        Args:
            file: Arquivo compactado contendo as imagens ou PDF
            file_extension: Extensão do arquivo (.zip, .rar, .7z, .tar, .pdf, etc.)
            
        Returns:
            Lista de caminhos para as imagens extraídas
            
        Raises:
            ValueError: Se nenhuma imagem válida for encontrada
        """
        try:
            # Se for PDF, usa método específico
            if file_extension == '.pdf':
                image_files = self._extract_pdf_pages(file)
                return (image_files, []) if collect_errors else image_files
            
            # Para outros formatos, extrai os arquivos para um diretório temporário
            extract_dir = self._extract_file(file, file_extension)
            
            # Lista todos os arquivos no diretório de extração
            all_files = []
            for root, _, files in os.walk(extract_dir):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    all_files.append(file_path)
            
            # Filtra apenas arquivos de imagem
            image_files, errors = self._filter_images(all_files, collect_errors=collect_errors)
            
            if not image_files:
                raise ValueError("Nenhuma imagem válida encontrada no arquivo")
                
            return (image_files, errors) if collect_errors else image_files
            
        except Exception as e:
            logger.error(f"Erro ao extrair imagens: {str(e)}", exc_info=True)
            raise ValueError(f"Falha ao extrair imagens: {str(e)}")
    
    def _filter_images(self, file_paths: List[str], collect_errors=False) -> Union[List[str], Tuple[List[str], list]]:
        """
        Filtra apenas arquivos de imagem válidos com base na extensão e conteúdo.
        
        Args:
            file_paths: Lista de caminhos de arquivo para filtrar
            
        Returns:
            Lista de caminhos para arquivos de imagem válidos
        """
        
        image_files = []
        errors = []
        
        for file_path in file_paths:
            fname = os.path.basename(file_path)
            # Ignorar arquivos ocultos ou não suportados
            if fname.startswith('.') or not any(fname.lower().endswith(ext) for ext in ALLOWED_IMAGE_EXTENSIONS):
                if collect_errors:
                    errors.append(f"Ignorado: {fname} (não suportado ou oculto)")
                continue
            try:
                # Verifica se o arquivo existe e tem tamanho maior que zero
                if not os.path.isfile(file_path):
                    logger.warning(f"Arquivo não encontrado: {file_path}")
                    continue
                    
                file_size = os.path.getsize(file_path)
                if file_size == 0:
                    logger.warning(f"Arquivo vazio: {file_path}")
                    continue
                    
                # Verifica o tamanho do arquivo
                if file_size > MAX_IMAGE_SIZE:
                    logger.warning(f"Arquivo muito grande: {file_path} ({file_size / (1024 * 1024):.2f}MB)")
                    if collect_errors:
                        errors.append(f"{fname}: Tamanho excede o limite de {MAX_IMAGE_SIZE//(1024*1024)}MB")
                    continue
                
                # Obtém a extensão do arquivo em minúsculas
                ext = os.path.splitext(file_path)[1].lower()
                
                # Verifica a extensão do arquivo
                if ext not in ALLOWED_IMAGE_EXTENSIONS:
                    logger.warning(f"Extensão não suportada: {file_path} ({ext})")
                    continue
                
                # Verifica se o arquivo é um diretório
                if os.path.isdir(file_path):
                    logger.warning(f"Ignorando diretório: {file_path}")
                    continue
                
                # Tenta abrir a imagem para verificar se é válida
                try:
                    with Image.open(file_path) as img:
                        # Para alguns formatos, precisamos carregar a imagem para verificar
                        img.load()
                        
                        # Verifica dimensões mínimas (opcional)
                        if img.width < 10 or img.height < 10:
                            continue
                            
                    # Se chegou até aqui, a imagem é válida
                    image_files.append(file_path)
                    
                except (IOError, OSError, UnidentifiedImageError, Image.DecompressionBombError):
                    # Ignora arquivos que não são imagens válidas ou muito grandes
                    continue
                
            except Exception as e:
                # Loga o erro mas continua processando outros arquivos
                logger.debug(f"Erro ao processar arquivo {file_path}: {str(e)}")
                if collect_errors:
                    errors.append(f"{fname}: {str(e)}")
                continue
                
        # Ordena as imagens por nome (ordem natural)
        image_files.sort(key=lambda x: self._natural_sort_key(os.path.basename(x)))
                
        return (image_files, errors) if collect_errors else image_files
    
    def _natural_sort_key(self, filename: str) -> list:
        """
        Gera uma chave para ordenação natural de strings contendo números.
        
        Exemplo:
            ['cap1', 'cap10', 'cap2'] -> ['cap', 1, 'cap', 10, 'cap', 2]
            
        Args:
            filename: Nome do arquivo para gerar a chave de ordenação
            
        Returns:
            Lista contendo strings e números para ordenação natural
        """
        import re
        return [
            int(text) if text.isdigit() else text.lower() 
            for text in re.split('([0-9]+)', str(Path(filename).stem))
        ]
    
    def _create_pages(self, chapter: Capitulo, image_files: List[str], collect_errors=False) -> list:
        """
        Cria as páginas do capítulo a partir dos arquivos de imagem.
        
        Este método processa cada imagem, otimiza-a para web e cria uma entrada de página
        no banco de dados associada ao capítulo.
        
        Args:
            chapter: Instância do modelo Capitulo
            image_files: Lista de caminhos para os arquivos de imagem
            
        Raises:
            ValueError: Se a lista de imagens estiver vazia ou se houver erro ao processar a primeira imagem
        """
        errors = []
        if not image_files:
            if collect_errors:
                errors.append("Nenhuma imagem fornecida para criar as páginas do capítulo")
            else:
                raise ValueError("Nenhuma imagem fornecida para criar as páginas do capítulo")
        
        # Ordena as imagens numericamente
        image_files.sort(key=lambda x: self._natural_sort_key(os.path.basename(x)))
        
        # Remove páginas existentes para evitar duplicação
        Pagina.objects.filter(capitulo=chapter).delete()
        
        for i, image_path in enumerate(image_files, 1):
            try:
                # Obtém a extensão do arquivo original
                file_ext = os.path.splitext(image_path)[1].lower()
                
                # Determina a extensão de saída com base no formato da imagem
                if file_ext in ['.webp', '.avif', '.heic', '.heif']:
                    output_ext = file_ext
                else:
                    output_ext = '.webp'  # Padrão para WebP
                
                # Otimiza a imagem
                optimized_image = self._optimize_image(image_path)
                
                # Cria a página no banco de dados
                pagina = Pagina(
                    capitulo=chapter,
                    number=i,
                )
                
                # Define o nome do arquivo com a extensão correta
                filename = f"cap_{chapter.number}_page_{i:03d}{output_ext}"
                
                # Salva a imagem otimizada
                pagina.image.save(
                    filename,
                    ContentFile(optimized_image.getvalue()),
                    save=False
                )
                
                # Salva a página no banco de dados
                pagina.save()
                
            except Exception as e:
                logger.error(f"Erro ao processar imagem {image_path}: {str(e)}")
                if collect_errors:
                    errors.append(f"{os.path.basename(image_path)}: {str(e)}")
                # Se for a primeira imagem e falhar, levanta a exceção
                if i == 1:
                    raise ValueError(f"Falha ao processar a primeira imagem: {str(e)}")
                # Para outras falhas, apenas registra e continua
                continue
        return errors

    def _optimize_image(self, image_path: str) -> BytesIO:
        """
        Otimiza uma imagem para exibição na web, reduzindo seu tamanho sem perder qualidade visível.
        
        Args:
            image_path: Caminho para o arquivo de imagem original
            
        Returns:
            BytesIO contendo a imagem otimizada
            
        Raises:
            ValueError: Se a imagem não puder ser aberta ou processada
        """
        from io import BytesIO
        
        try:
            # Determina o formato de saída com base na extensão original
            file_ext = os.path.splitext(image_path)[1].lower()
            output_format = 'WEBP'  # Padrão para WebP (melhor relação qualidade/tamanho)
            
            # Se a imagem já for WebP ou não for um formato comum, mantém o formato original
            if file_ext in ['.webp', '.avif', '.heic', '.heif']:
                output_format = file_ext[1:].upper()
            
            # Tenta abrir a imagem, lidando com formatos especiais
            try:
                img = Image.open(image_path)
                
                # Para formatos que precisam de tratamento especial
                if file_ext in ['.heic', '.heif']:
                    # Converte HEIC/HEIF para RGB usando Pillow-HEIF se disponível
                    try:
                        import pillow_heif
                        pillow_heif.register_heif_opener()
                        img = Image.open(image_path).convert('RGB')
                    except ImportError:
                        logger.warning("Pillow-HEIF não está instalado. A conversão de HEIC/HEIF pode não funcionar corretamente.")
                        img = img.convert('RGB')
                
                # Preserva o modo de cor original (RGB, RGBA, L, etc.)
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')
                
                # Redimensiona imagens muito grandes (máx 2000px no maior lado)
                max_size = 2000
                if max(img.size) > max_size:
                    ratio = max_size / max(img.size)
                    new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Configurações de otimização
                save_kwargs = {}
                
                # Configurações específicas por formato
                if output_format == 'JPEG':
                    save_kwargs.update({
                        'quality': 85,  # 0-100, 85 é um bom equilíbrio
                        'progressive': True,  # Carregamento progressivo para JPEG
                        'optimize': True,
                    })
                elif output_format == 'WEBP':
                    save_kwargs.update({
                        'quality': 80,  # 0-100
                        'method': 6,  # 0-6, 6 é a melhor qualidade de compressão
                        'lossless': False,  # Compressão com perdas para melhor tamanho
                    })
                elif output_format == 'PNG':
                    save_kwargs.update({
                        'compress_level': 6,  # 0-9, 9 é compressão máxima
                        'optimize': True,
                    })
                elif output_format == 'AVIF':
                    # AVIF requer Pillow 8.0+ com suporte a AVIF
                    save_kwargs.update({
                        'quality': 80,  # 0-100
                        'lossless': False,
                    })
                
                # Salva a imagem em memória
                output = BytesIO()
                img.save(output, format=output_format, **save_kwargs)
                output.seek(0)
                
                # Verifica se a imagem foi salva corretamente
                if output.getbuffer().nbytes == 0:
                    raise ValueError("Falha ao salvar a imagem otimizada (tamanho zero)")
                    
                return output
                
            except Exception as img_error:
                logger.error(f"Erro ao processar imagem {image_path}: {str(img_error)}", exc_info=True)
                raise ValueError(f"Formato de imagem não suportado ou corrompido: {file_ext}")
                
                return output
                
        except Exception as e:
            logger.error(f"Erro ao otimizar imagem {image_path}: {str(e)}", exc_info=True)
            raise ValueError(f"Falha ao processar a imagem: {str(e)}")

    def _create_temp_dir(self) -> str:
        # Depreciado: não é mais necessário
        return None

    def _cleanup_temp_dir(self):
        # Depreciado: não é mais necessário
        pass