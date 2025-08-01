"""
Serviço para processamento de arquivos de volumes de mangá.

Este módulo contém a implementação concreta do serviço de processamento de arquivos
que extrai páginas de imagens de vários formatos de arquivo compactado para volumes.
"""
import logging
import os
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set, Any, BinaryIO, Union

from django.core.files import File
from django.core.files.storage import default_storage
from django.db import transaction
from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError, ImageFile

# Importa os modelos necessários
from ..models import Volume, Capitulo, Pagina

# Tenta importar bibliotecas opcionais
try:
    import rarfile
except ImportError:
    rarfile = None

try:
    import py7zr
except ImportError:
    py7zr = None
    
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

# Configura o Pillow para processar imagens grandes
ImageFile.LOAD_TRUNCATED_IMAGES = True

# Extensões de imagem permitidas
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']

logger = logging.getLogger(__name__)

class VolumeFileProcessorService:
    """
    Serviço para processar arquivos de volumes de mangá.
    
    Esta classe é responsável por extrair e processar páginas de imagens
    a partir de arquivos compactados (ZIP, RAR, 7Z) ou PDFs.
    """
    
    # Tamanho máximo de arquivo permitido (100MB)
    MAX_ARCHIVE_SIZE = 100 * 1024 * 1024
    
    # Número mínimo e máximo de páginas permitidas
    MIN_PAGES = 1
    MAX_PAGES = 2000
    
    # Extensões de imagem suportadas
    IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    
    # Formatos de arquivo suportados
    SUPPORTED_FORMATS = ['.zip', '.rar', '.7z', '.cbz', '.cbr', '.cb7']
    
    # Arquivos a serem ignorados
    IGNORED_FILES = ['.DS_Store', 'Thumbs.db', 'desktop.ini']
    MAX_PAGES = 1000
    
    def __init__(self):
        """Inicializa o serviço com um diretório temporário vazio."""
        self.temp_dir = None
        self.logger = logging.getLogger(__name__)
    
    def process_volume_file(self, volume, file_path: str) -> Tuple[bool, str]:
        """
        Processa um arquivo de volume e cria as páginas correspondentes.
        
        Args:
            volume: Instância do modelo Volume
            file_path: Caminho para o arquivo a ser processado
            
        Returns:
            Tupla (success, message) indicando o resultado da operação
            
        Raises:
            ValueError: Se o volume não for válido
            ValidationError: Se o arquivo não for um formato suportado
        """
        if not hasattr(volume, 'pk') or not volume.pk:
            raise ValueError("O parâmetro 'volume' deve ser uma instância de Volume válida")
        
        # Verifica se o arquivo existe
        if not os.path.isfile(file_path):
            error_msg = f"Arquivo não encontrado: {file_path}"
            logger.error(error_msg)
            return False, error_msg
        from pathlib import Path
        
        # Estrutura para armazenar os arquivos extraídos
        extracted_files = {}
        
        # Obtém o nome do arquivo para logging
        file_name = os.path.basename(file_path)
        logger.info(f"Iniciando extração do arquivo: {file_name}")
        
        # Verifica se o arquivo tem uma extensão suportada
        file_name_lower = file_name.lower()
        supported_extensions = ['.zip', '.rar', '.7z', '.cbz', '.cbr', '.cb7']
        if not any(file_name_lower.endswith(ext) for ext in supported_extensions):
            error_msg = f"Formato de arquivo não suportado: {file_name}. Formatos suportados: {', '.join(supported_extensions)}"
            logger.error(error_msg)
            return False, error_msg
        
        # Verifica o tamanho do arquivo
        try:
            file_size = os.path.getsize(file_path)
            if file_size > self.MAX_ARCHIVE_SIZE:
                error_msg = f"Arquivo muito grande. Tamanho máximo permitido: {self.MAX_ARCHIVE_SIZE/1024/1024:.2f}MB"
                logger.error(error_msg)
                return False, error_msg
                
            # Cria um diretório temporário para extração
            self.temp_dir = tempfile.mkdtemp(prefix='manga_volume_')
            logger.info(f"Diretório temporário criado: {self.temp_dir}")
            
            # Processa o arquivo com base na extensão
            if file_name_lower.endswith(('.zip', '.cbz')):
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    # Extrai todos os arquivos
                    zip_ref.extractall(self.temp_dir)
                    
                    # Mapeia a estrutura de diretórios
                    for file_path in zip_ref.namelist():
                        self._add_to_file_structure(extracted_files, file_path)
                        
                success, message = self._process_extracted_images(volume, self.temp_dir)
                return success, message
                
            elif file_name_lower.endswith(('.rar', '.cbr')) and rarfile is not None:
                with rarfile.RarFile(file_path, 'r') as rar_ref:
                    rar_ref.extractall(self.temp_dir)
                    for file_path in rar_ref.namelist():
                        self._add_to_file_structure(extracted_files, file_path)
                
                success, message = self._process_extracted_images(volume, self.temp_dir)
                return success, message
                
            elif file_name_lower.endswith(('.7z', '.cb7')) and py7zr is not None:
                with py7zr.SevenZipFile(file_path, 'r') as seven_zip_ref:
                    seven_zip_ref.extractall(self.temp_dir)
                    for file_path in seven_zip_ref.getnames():
                        self._add_to_file_structure(extracted_files, file_path)
                
                success, message = self._process_extracted_images(volume, self.temp_dir)
                return success, message
                
            else:
                error_msg = "Formato de arquivo não suportado ou biblioteca necessária não encontrada"
                logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Erro ao processar o arquivo: {str(e)}"
            logger.exception(error_msg)
            return False, error_msg
            
        finally:
            # Limpa os arquivos temporários
            self._cleanup_temp_dir()
                        
    def _extract_zip(self, file_path: str) -> List[str]:
        """
        Extrai arquivos de um arquivo ZIP.
        
        Args:
            file_path: Caminho para o arquivo ZIP
            
        Returns:
            Lista de caminhos para os arquivos extraídos
            
        Raises:
            ValueError: Se o arquivo não for um ZIP válido ou estiver corrompido
        """
        extracted_files = []
        
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Cria um diretório temporário para extração
                self.temp_dir = tempfile.mkdtemp(prefix='manga_extract_')
                
                # Extrai todos os arquivos
                zip_ref.extractall(self.temp_dir)
                
                # Lista todos os arquivos extraídos
                for root, _, files in os.walk(self.temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if self._is_valid_file(file_path):
                            extracted_files.append(file_path)
                
                return extracted_files
                
        except zipfile.BadZipFile as e:
            self._cleanup_temp_dir()
            raise ValueError(f"Arquivo ZIP inválido ou corrompido: {str(e)}")
        except Exception as e:
            self._cleanup_temp_dir()
            raise ValueError(f"Erro ao extrair arquivo ZIP: {str(e)}")
    
    def _extract_7z(self, file_path: str) -> List[str]:
        """
        Extrai arquivos de um arquivo 7Z.
        
        Args:
            file_path: Caminho para o arquivo 7Z
            
        Returns:
            Lista de caminhos para os arquivos extraídos
            
        Raises:
            ValueError: Se o arquivo não for um 7Z válido, estiver corrompido
                      ou se a biblioteca py7zr não estiver instalada
        """
        if py7zr is None:
            raise ImportError("A biblioteca 'py7zr' é necessária para extrair arquivos 7Z")
            
        extracted_files = []
        
        try:
            with py7zr.SevenZipFile(file_path, 'r') as seven_zip_ref:
                # Cria um diretório temporário para extração
                self.temp_dir = tempfile.mkdtemp(prefix='manga_extract_')
                
                # Extrai todos os arquivos
                seven_zip_ref.extractall(self.temp_dir)
                
                # Lista todos os arquivos extraídos
                for root, _, files in os.walk(self.temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if self._is_valid_file(file_path):
                            extracted_files.append(file_path)
                
                return extracted_files
                
        except Exception as e:
            self._cleanup_temp_dir()
            raise ValueError(f"Erro ao extrair arquivo 7Z: {str(e)}")
    
    def _add_to_file_structure(self, file_structure: dict, file_path: str) -> None:
        """
        Adiciona um arquivo à estrutura de diretórios.
        
        Args:
            file_structure: Dicionário com a estrutura de arquivos
            file_path: Caminho do arquivo a ser adicionado
        """
        # Ignora pastas vazias
        if not file_path.strip() or file_path.endswith('/'):
            return
            
        # Divide o caminho em partes
        parts = [p for p in Path(file_path).parts if p and p != '.']
        
        # Se não houver partes, ignora
        if not parts:
            return
            
        # O primeiro nível é considerado o nome da pasta do capítulo
        chapter_folder = parts[0]
        
        # Inicializa a lista de arquivos para esta pasta de capítulo se não existir
        if chapter_folder not in file_structure:
            file_structure[chapter_folder] = []
        
        # Adiciona o arquivo à lista do capítulo
        file_structure[chapter_folder].append(file_path)
    
    def _update_volume_cache(self, volume: Volume) -> None:
        """
        Atualiza o cache para o volume processado.
        
        Args:
            volume: Instância do Volume que foi processado
        """
        from django.core.cache import cache
        from django.utils import timezone
        
        try:
            # Atualiza o timestamp de atualização do volume
            cache_key = f'manga_volume_{volume.id}_updated'
            cache.set(cache_key, timezone.now(), timeout=60*60*24*7)  # Cache por 7 dias
            
            # Invalida o cache de listagem de volumes para o mangá
            cache.delete_pattern(f'manga_{volume.manga_id}_volumes_*')
            
            logger.debug(f"Cache atualizado para o volume {volume.id}")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar o cache do volume {volume.id}: {str(e)}", 
                        exc_info=True)
    
    def _process_chapters(self, volume: Volume, base_dir: str, extracted_files: Dict[str, List[str]]) -> Tuple[bool, str]:
        """
        Processa os capítulos extraídos e cria os registros no banco de dados.
        
        Args:
            volume: Instância do Volume
            base_dir: Diretório base onde os arquivos foram extraídos
            extracted_files: Dicionário com a estrutura de pastas/arquivos
            
        Returns:
            Tupla (success, message) indicando o resultado da operação
        """
        from django.db import transaction
        from pathlib import Path
        import shutil
        
        success_count = 0
        error_messages = []
        temp_dir = base_dir  # Armazena o diretório temporário para limpeza posterior
        
        try:
            # Ordena as pastas de capítulos numericamente
            chapter_folders = sorted(
                extracted_files.keys(),
                key=lambda x: self._extract_chapter_number(x) or 0  # Usa 0 se não conseguir extrair o número
            )
            
            with transaction.atomic():
                for folder_name in chapter_folders:
                    try:
                        # Extrai o número do capítulo do nome da pasta
                        chapter_number = self._extract_chapter_number(folder_name)
                        if chapter_number is None:
                            error_messages.append(f"Não foi possível determinar o número do capítulo para a pasta: {folder_name}")
                            continue
                        
                        # Cria um diretório temporário para o capítulo
                        chapter_temp_dir = os.path.join(base_dir, f"chapter_{chapter_number}")
                        os.makedirs(chapter_temp_dir, exist_ok=True)
                        
                        # Copia os arquivos para o diretório temporário
                        file_paths = extracted_files[folder_name]
                        for file_path in file_paths:
                            src_path = os.path.join(base_dir, file_path)
                            if os.path.isfile(src_path):
                                dest_path = os.path.join(chapter_temp_dir, os.path.basename(file_path))
                                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                                shutil.copy2(src_path, dest_path)
                        
                        # Cria o capítulo a partir da pasta
                        success, message = self._create_chapter_from_folder(volume, chapter_number, chapter_temp_dir)
                        
                        if success:
                            success_count += 1
                            logger.info(f"Capítulo {chapter_number} processado com sucesso: {message}")
                            self._update_chapter_cache(volume, chapter_number)
                        else:
                            error_messages.append(f"Erro no capítulo {chapter_number}: {message}")
                            
                    except Exception as e:
                        error_msg = f"Erro ao processar capítulo {folder_name}: {str(e)}"
                        logger.error(error_msg, exc_info=True)
                        error_messages.append(error_msg)
                        # Continua para o próximo capítulo mesmo em caso de erro
                        continue
                    finally:
                        # Limpa o diretório temporário do capítulo
                        try:
                            if os.path.exists(chapter_temp_dir):
                                shutil.rmtree(chapter_temp_dir, ignore_errors=True)
                        except Exception as e:
                            logger.warning(f"Falha ao limpar diretório temporário {chapter_temp_dir}: {str(e)}")
                            # Não interrompe o fluxo em caso de falha na limpeza
            
            # Prepara a mensagem de resultado
            if success_count > 0:
                result_message = f"{success_count} capítulo(s) processado(s) com sucesso."
                if error_messages:
                    result_message += f" Erros: {' | '.join(error_messages)}"
                
                # Atualiza o cache do volume após processar todos os capítulos
                self._update_volume_cache(volume)
                
                return True, result_message
            else:
                return False, "Nenhum capítulo foi processado com sucesso. " + " | ".join(error_messages)
                
        except Exception as e:
            error_msg = f"Erro inesperado ao processar capítulos: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg
            
        finally:
            # Garante que os arquivos temporários sejam limpos mesmo em caso de erro
            if 'temp_dir' in locals():
                self._cleanup_temp_files(temp_dir)
    
    def _extract_chapter_number(self, folder_name: str) -> Optional[float]:
        """
        Extrai o número do capítulo a partir do nome da pasta.
        
        Args:
            folder_name: Nome da pasta do capítulo (ex: 'capitulo_1', 'ch001', '1', etc.)
            
        Returns:
            Número do capítulo como float ou None se não for possível extrair
        """
        import re
        
        # Tenta extrair números no final do nome da pasta
        match = re.search(r'(?:(?:cap(?:itulo)?|ch(?:apter)?[\s_-]*)?)(\d+(?:\.\d+)?)', folder_name, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except (ValueError, TypeError):
                pass
                
        # Se não encontrar no formato esperado, tenta extrair apenas os dígitos
        digits = re.sub(r'[^\d.]', '', folder_name)
        if digits:
            try:
                return float(digits) if '.' in digits else int(digits)
            except (ValueError, TypeError):
                pass
                
        return None
    
    def _process_chapter_files(self, chapter: Capitulo, file_paths: List[str], base_dir: str, dest_dir: str) -> Tuple[bool, str]:
        """
        Processa os arquivos de um capítulo e cria as páginas.
        
        Args:
            chapter: Instância do Capítulo
            file_paths: Lista de caminhos de arquivo no capítulo
            base_dir: Diretório base onde os arquivos foram extraídos
            dest_dir: Diretório de destino para os arquivos processados
            
        Returns:
            Tupla (success, message) indicando o resultado da operação
        """
        from django.core.files import File
        from ..models import Pagina
        import shutil
        
        try:
            # Filtra apenas arquivos de imagem válidos
            image_files = []
            for file_path in file_paths:
                file_name = os.path.basename(file_path).lower()
                if any(file_name.endswith(ext) for ext in ALLOWED_IMAGE_EXTENSIONS):
                    image_files.append(file_path)
            
            if not image_files:
                return False, "Nenhuma imagem válida encontrada no capítulo."
            
            # Ordena os arquivos numericamente
            image_files.sort(key=lambda x: self._extract_page_number(os.path.basename(x)))
            
            # Cria as páginas no banco de dados
            for i, file_path in enumerate(image_files, 1):
                # Caminho completo do arquivo de origem
                src_path = os.path.join(base_dir, file_path)
                
                # Cria o diretório de destino se não existir
                os.makedirs(dest_dir, exist_ok=True)
                
                # Nome do arquivo de destino
                dest_filename = f"page_{i:03d}{os.path.splitext(file_path)[1].lower()}"
                dest_path = os.path.join(dest_dir, dest_filename)
                
                # Copia o arquivo para o diretório de destino
                shutil.copy2(src_path, dest_path)
                
                # Cria o registro da página no banco de dados
                with open(dest_path, 'rb') as f:
                    page = Pagina(
                        capitulo=chapter,
                        numero=i,
                        imagem=File(f, name=dest_filename)
                    )
                    page.save()
            
            return True, f"{len(image_files)} páginas processadas"
            
        except Exception as e:
            error_msg = f"Erro ao processar arquivos do capítulo: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg
    
    def _extract_page_number(self, filename: str) -> int:
        """
        Extrai o número da página a partir do nome do arquivo.
        
        Args:
            filename: Nome do arquivo da página
            
        Returns:
            Número da página como inteiro
        """
        import re
        
        # Tenta extrair número no final do nome do arquivo
        match = re.search(r'(?:page|p|pg|pagina)?[\s_-]*(\d+)', filename, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, TypeError):
                pass
                
        # Se não encontrar, retorna um número alto para colocar no final
        return 9999
    
    def _update_chapter_cache(self, volume: Volume, chapter_number: int) -> None:
        """
        Atualiza o cache para o capítulo processado.
        
        Args:
            volume: Instância do Volume
            chapter_number: Número do capítulo processado
        """
        from django.core.cache import cache
        from django.utils import timezone
        
        try:
            # Gera uma chave de cache única para o capítulo
            cache_key = f'manga_volume_{volume.id}_chapter_{chapter_number}_updated'
            
            # Atualiza o timestamp de atualização no cache
            cache.set(cache_key, timezone.now(), timeout=60*60*24*7)  # Cache por 7 dias
            
            # Invalida o cache de listagem de capítulos para este volume
            cache.delete_pattern(f'manga_volume_{volume.id}_chapters_*')
            
            logger.debug(f"Cache atualizado para o capítulo {chapter_number} do volume {volume.id}")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar o cache para o capítulo {chapter_number}: {str(e)}", 
                        exc_info=True)
    
    def _cleanup_temp_files(self, temp_dir: str) -> None:
        """
        Limpa os arquivos temporários de forma segura.
        
        Args:
            temp_dir: Caminho para o diretório temporário
        """
        import shutil
        import time
        
        if not temp_dir or not os.path.isdir(temp_dir):
            return
            
        try:
            # Tenta remover o diretório várias vezes em caso de bloqueio de arquivo
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    if not os.path.exists(temp_dir):
                        logger.debug(f"Diretório temporário removido com sucesso: {temp_dir}")
                        break
                    
                    logger.warning(f"Falha ao remover diretório temporário (tentativa {attempt + 1}/{max_attempts}): {temp_dir}")
                    if attempt < max_attempts - 1:  # Não dormir na última tentativa
                        time.sleep(1)  # Espera 1 segundo antes de tentar novamente
                        
                except Exception as e:
                    logger.warning(f"Erro ao remover diretório temporário (tentativa {attempt + 1}/{max_attempts}): {str(e)}")
                    if attempt == max_attempts - 1:  # Última tentativa
                        logger.error(f"Falha ao remover diretório temporário após {max_attempts} tentativas: {temp_dir}", 
                                   exc_info=True)
        except Exception as e:
            logger.error(f"Erro inesperado durante a limpeza de arquivos temporários: {str(e)}", 
                        exc_info=True)
    
    def _create_chapter_from_folder(self, volume: Volume, chapter_number: int, folder_path: str) -> Tuple[bool, str]:
        """
        Cria um capítulo a partir de uma pasta de imagens.
        
        Args:
            volume: Instância do Volume
            chapter_number: Número do capítulo
            folder_path: Caminho para a pasta contendo as imagens do capítulo
            
        Returns:
            Tupla (success, message) indicando o resultado da operação
        """
        from django.core.files import File
        from ..models import Capitulo, Pagina
        import os
        
        try:
            # Verifica se o diretório existe
            if not os.path.isdir(folder_path):
                return False, f"Diretório não encontrado: {folder_path}"
            
            # Lista todos os arquivos de imagem no diretório
            image_files = []
            for filename in os.listdir(folder_path):
                if any(filename.lower().endswith(ext) for ext in ALLOWED_IMAGE_EXTENSIONS):
                    image_files.append(filename)
            
            if not image_files:
                return False, f"Nenhuma imagem válida encontrada no diretório: {folder_path}"
            
            # Ordena os arquivos numericamente
            image_files.sort(key=lambda x: self._extract_page_number(x))
            
            # Cria ou atualiza o capítulo
            chapter, created = Capitulo.objects.get_or_create(
                volume=volume,
                number=chapter_number,
                defaults={
                    'title': f"Capítulo {chapter_number}",
                    'is_published': volume.is_published
                }
            )
            
            # Se o capítulo já existia, remove as páginas antigas
            if not created:
                chapter.paginas.all().delete()
            
            # Cria as páginas do capítulo
            for i, filename in enumerate(image_files, 1):
                file_path = os.path.join(folder_path, filename)
                
                # Verifica se o arquivo existe e é um arquivo válido
                if not os.path.isfile(file_path):
                    logger.warning(f"Arquivo não encontrado: {file_path}")
                    continue
                
                # Cria o registro da página no banco de dados
                with open(file_path, 'rb') as f:
                    page = Pagina(
                        capitulo=chapter,
                        numero=i,
                        imagem=File(f, name=os.path.basename(filename))
                    )
                    page.save()
            
            return True, f"Capítulo {chapter_number} criado com {len(image_files)} páginas"
            
        except Exception as e:
            error_msg = f"Erro ao criar capítulo a partir da pasta {folder_path}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg
        
    def _process_volume_file(self, volume: Volume, file_path: str) -> Tuple[bool, str]:
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

    def _process_volume_file(self, volume: Volume, file_path: str) -> Tuple[bool, str]:
        # Verifica se o volume é válido
        if not hasattr(volume, 'pk') or not volume.pk:
            raise ValueError("O parâmetro 'volume' deve ser uma instância de Volume válida")

        # Verifica se o arquivo existe
        if not os.path.isfile(file_path):
            error_msg = f"Arquivo não encontrado: {file_path}"
            logger.error(error_msg)
            return False, error_msg
            
        # Verifica a extensão do arquivo
        file_ext = os.path.splitext(file_path)[1].lower()
        supported_extensions = ['.zip', '.rar', '.7z', '.cbz', '.cbr', '.cb7']
        
        if file_ext not in supported_extensions:
            error_msg = f"Formato de arquivo não suportado: {file_ext}. Formatos suportados: {', '.join(supported_extensions)}"
            logger.error(error_msg)
            return False, error_msg
            
        try:
            # Cria um diretório temporário para extração
            self.temp_dir = tempfile.mkdtemp(prefix='manga_volume_')
            logger.info(f"Diretório temporário criado: {self.temp_dir}")
            
            # Processa o arquivo com base na extensão
            if file_ext in ['.zip', '.cbz']:
                extracted_files = self._extract_zip(file_path)
            elif file_ext in ['.rar', '.cbr'] and rarfile is not None:
                extracted_files = self._extract_rar(file_path)
            elif file_ext in ['.7z', '.cb7'] and py7zr is not None:
                extracted_files = self._extract_7z(file_path)
            else:
                error_msg = "Formato de arquivo não suportado ou biblioteca necessária não encontrada"
                logger.error(error_msg)
                return False, error_msg
                
            # Processa as imagens extraídas
            success, message = self._process_extracted_images(volume, self.temp_dir)
            return success, message
            
        except Exception as e:
            error_msg = f"Erro ao processar o arquivo: {str(e)}"
            logger.exception(error_msg)
            return False, error_msg
            
        finally:
            # Limpa os arquivos temporários
            # CORRIGIDO: Usar o método correto que existe
            if hasattr(self, 'temp_dir') and self.temp_dir:
                self._cleanup_temp_files(self.temp_dir)
                logger.info(f"Diretório temporário removido: {self.temp_dir}")

    def _process_extracted_images(self, volume: Volume, base_dir: str = None) -> Tuple[bool, str]:
        """Processa as imagens extraídas e cria as páginas no banco de dados."""
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
            # ✅ ADICIONADO: Transação atômica para rollback em caso de erro
            with transaction.atomic():
                # Cria um capítulo para o volume
                capitulo = Capitulo.objects.create(
                    volume=volume,
                    number=1,
                    title=f"Volume {volume.number}",
                    is_published=volume.is_published
                )
                
                # Processa cada imagem
                for i, img_path in enumerate(image_files, start=1):
                    try:
                        with Image.open(img_path) as img:
                            # ✅ CORRIGIDO: Usar Django File system em vez de path hardcoded
                            from django.core.files.base import ContentFile
                            from io import BytesIO
                            
                            # Cria arquivo em memória
                            img_io = BytesIO()
                            img_format = 'JPEG' if img_path.lower().endswith(('.jpg', '.jpeg')) else 'PNG'
                            img.save(img_io, format=img_format, quality=85, optimize=True)
                            img_io.seek(0)
                            
                            # Gera nome do arquivo
                            filename = f"page_{i:03d}{os.path.splitext(img_path)[1]}"
                            django_file = ContentFile(img_io.getvalue(), name=filename)
                            
                            # ✅ CORRIGIDO: Usar nomes corretos dos campos
                            Pagina.objects.create(
                                capitulo=capitulo,
                                number=i,  # ✅ Campo correto
                                image=django_file,  # ✅ Campo correto + Django File
                                width=img.width,  # ✅ Campo correto
                                height=img.height,  # ✅ Campo correto
                                file_size=len(img_io.getvalue())  # ✅ Tamanho correto
                            )
                            
                    except (UnidentifiedImageError, OSError) as e:
                        logger.warning(f"Não foi possível processar a imagem {img_path}: {str(e)}")
                        continue
                
                return True, f"Volume processado com sucesso. {len(image_files)} páginas adicionadas."
                
        except Exception as e:
            logger.exception("Erro ao processar imagens extraídas")
            return False, f"Erro ao processar imagens: {str(e)}"
