"""
Serviço para processamento de arquivos de capítulos de mangá.

Este módulo contém a implementação concreta do serviço de processamento de arquivos
que extrai páginas de imagens de vários formatos de arquivo compactado.
"""
from io import BytesIO
import os
import zipfile
import rarfile
import tarfile
import py7zr
import tempfile
import shutil
from pathlib import Path
from typing import List, Tuple, Optional, BinaryIO, Union
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from PIL import Image, UnidentifiedImageError, ImageFile
import logging

from ..constants import ALLOWED_IMAGE_EXTENSIONS, ALLOWED_ARCHIVE_EXTENSIONS
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
        '.txz', '.cb7', '.cbt', '.cba'
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
            # Cria um diretório temporário para extração
            self._create_temp_dir()
            
            # Extrai as imagens do arquivo
            image_files = self._extract_images(file, file_extension if not is_temp_zip else '.zip')
            
            if not image_files:
                return False, "Nenhuma imagem válida encontrada no arquivo ou pasta"
                
            # Cria as páginas no banco de dados
            self._create_pages(chapter, image_files)
            return True, f"Capítulo processado com sucesso. {len(image_files)} páginas criadas a partir do {'arquivo' if not is_temp_zip else 'conteúdo da pasta'}."
            
        except Exception as e:
            logger.error(f"Erro ao processar arquivo do capítulo: {str(e)}", exc_info=True)
            return False, f"Erro ao processar arquivo: {str(e)}"
            
        finally:
            # Garante que o diretório temporário seja limpo em caso de erro
            self._cleanup_temp_dir()
    
    def _extract_file(self, file: BinaryIO, file_extension: str) -> str:
        """
        Extrai o conteúdo de um arquivo compactado para um diretório temporário.
        
        Args:
            file: Arquivo compactado
            file_extension: Extensão do arquivo (.zip, .rar, .7z, .tar, etc.)
            
        Returns:
            Caminho para o diretório temporário com os arquivos extraídos
            
        Raises:
            ValueError: Se o formato do arquivo não for suportado
            RuntimeError: Se ocorrer um erro ao extrair o arquivo
        """
        try:
            # Salva o arquivo temporariamente
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)
            for chunk in file.chunks():
                temp_file.write(chunk)
            temp_file.close()
            
            # Cria um diretório temporário para extração
            extract_dir = os.path.join(tempfile.gettempdir(), f'manga_extract_{os.urandom(8).hex()}')
            os.makedirs(extract_dir, exist_ok=True)
            
            # Extrai o arquivo baseado na extensão
            try:
                if file_extension in ['.zip', '.cbz']:
                    with zipfile.ZipFile(temp_file.name, 'r') as zip_ref:
                        zip_ref.extractall(extract_dir)
                
                elif file_extension in ['.rar', '.cbr']:
                    with rarfile.RarFile(temp_file.name, 'r') as rar_ref:
                        rar_ref.extractall(extract_dir)
                        
                elif file_extension in ['.7z', '.cb7']:
                    with py7zr.SevenZipFile(temp_file.name, mode='r') as sz_ref:
                        sz_ref.extractall(ext_dir=extract_dir)
                        
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
                
                elif file_extension in ['.7z', '.cb7']:
                    with py7zr.SevenZipFile(temp_file.name, mode='r') as sz_ref:
                        sz_ref.extractall(extract_dir)
                
                elif file_extension in ['.tar', '.cbt']:
                    with tarfile.open(temp_file.name, 'r') as tar_ref:
                        tar_ref.extractall(extract_dir)
                
                elif file_extension in ['.tar.gz', '.tgz']:
                    with tarfile.open(temp_file.name, 'r:gz') as tar_ref:
                        tar_ref.extractall(extract_dir)
                
                elif file_extension in ['.tar.bz2', '.tbz2']:
                    with tarfile.open(temp_file.name, 'r:bz2') as tar_ref:
                        tar_ref.extractall(extract_dir)
                
                elif file_extension in ['.tar.xz', '.txz']:
                    with tarfile.open(temp_file.name, 'r:xz') as tar_ref:
                        tar_ref.extractall(extract_dir)
                
                else:
                    raise ValueError(f"Formato de arquivo não suportado: {file_extension}")
                
                return extract_dir
                
            except Exception as extract_error:
                # Se a extração falhar, tenta identificar o erro específico
                if 'password required' in str(extract_error).lower():
                    raise RuntimeError("Arquivo protegido por senha não é suportado")
                elif 'not a zip file' in str(extract_error).lower():
                    raise RuntimeError("Arquivo corrompido ou em formato inválido")
                elif 'bad magic number' in str(extract_error).lower():
                    raise RuntimeError("Formato de arquivo inválido ou corrompido")
                else:
                    raise extract_error
            
        except Exception as e:
            # Log detalhado do erro
            logger.error(f"Erro ao extrair arquivo {file_extension}: {str(e)}", exc_info=True)
            
            # Limpa o diretório temporário em caso de erro
            if 'extract_dir' in locals() and os.path.exists(extract_dir):
                shutil.rmtree(extract_dir, ignore_errors=True)
            
            # Mensagens de erro mais amigáveis
            if 'No such file or directory' in str(e):
                raise RuntimeError("Arquivo não encontrado ou inacessível")
            elif 'Invalid data' in str(e):
                raise RuntimeError("Dados inválidos no arquivo")
            else:
                raise RuntimeError(f"Erro ao processar o arquivo: {str(e)}")
            
        finally:
            # Remove o arquivo temporário
            if 'temp_file' in locals() and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except Exception as e:
                    logger.warning(f"Não foi possível remover arquivo temporário {temp_file.name}: {str(e)}")
    
    def _extract_images(self, file: BinaryIO, file_extension: str) -> List[str]:
        """
        Extrai imagens de um arquivo compactado.
        
        Args:
            file: Arquivo compactado contendo as imagens
            file_extension: Extensão do arquivo (.zip, .rar, .7z, .tar, etc.)
            
        Returns:
            Lista de caminhos para as imagens extraídas
            
        Raises:
            ValueError: Se nenhuma imagem válida for encontrada
        """
        try:
            # Extrai os arquivos para um diretório temporário
            extract_dir = self._extract_file(file, file_extension)
            
            # Lista todos os arquivos no diretório de extração
            all_files = []
            for root, _, files in os.walk(extract_dir):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    all_files.append(file_path)
            
            # Filtra apenas arquivos de imagem
            image_files = self._filter_images(all_files)
            
            if not image_files:
                raise ValueError("Nenhuma imagem válida encontrada no arquivo")
                
            return image_files
            
        except Exception as e:
            logger.error(f"Erro ao extrair imagens: {str(e)}", exc_info=True)
            raise ValueError(f"Falha ao extrair imagens: {str(e)}")
    
    def _filter_images(self, file_paths: List[str]) -> List[str]:
        """
        Filtra apenas arquivos de imagem válidos com base na extensão e conteúdo.
        
        Args:
            file_paths: Lista de caminhos de arquivo para filtrar
            
        Returns:
            Lista de caminhos para arquivos de imagem válidos
        """
        from ..constants import ALLOWED_IMAGE_EXTENSIONS, MESSAGES, MAX_IMAGE_SIZE
        
        image_files = []
        
        for file_path in file_paths:
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
                        img.verify()  # Verifica se é uma imagem válida
                        
                        # Para formatos que não suportam verify(), tentamos carregar a imagem
                        try:
                            img.load()
                        except (IOError, OSError):
                            # Se não conseguir carregar, ignora o arquivo
                            continue
                        
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
                continue
                
        # Ordena as imagens por nome (ordem natural)
        if image_files:
            image_files.sort(key=lambda x: self._natural_sort_key(os.path.basename(x)))
                
        return image_files
    
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
    
    def _create_pages(self, chapter: Capitulo, image_files: List[str]) -> None:
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
        if not image_files:
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
                
                logger.debug(f"Página {i} criada com sucesso a partir de {os.path.basename(image_path)}")
                
            except Exception as e:
                logger.error(f"Erro ao processar imagem {image_path}: {str(e)}", exc_info=True)
                # Se for a primeira imagem e falhar, levanta a exceção
                if i == 1:
                    raise ValueError(f"Falha ao processar a primeira imagem: {str(e)}")
                # Para outras falhas, apenas registra e continua
                continue

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
        """
        Cria um diretório temporário para extração de arquivos.
        
        Returns:
            Caminho para o diretório temporário criado
        """
        if not self.temp_dir or not os.path.exists(self.temp_dir):
            self.temp_dir = tempfile.mkdtemp(prefix='manga_processor_')
            logger.debug(f"Diretório temporário criado: {self.temp_dir}")
        return self.temp_dir
        
    def _cleanup_temp_dir(self):
        """
        Remove o diretório temporário e seu conteúdo, se existir.
        
        Este método é seguro para ser chamado múltiplas vezes e mesmo se o diretório
        não existir mais.
        """
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                logger.debug(f"Diretório temporário removido: {self.temp_dir}")
            except Exception as e:
                logger.warning(f"Falha ao remover diretório temporário {self.temp_dir}: {str(e)}")
            finally:
                self.temp_dir = None