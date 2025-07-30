"""
Serviço para processamento de arquivos compactados de volumes de mangá.

Este módulo contém a implementação do serviço que processa arquivos compactados
contendo múltiplos capítulos organizados em pastas.
"""
import os
import logging
import tempfile
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set, BinaryIO
from django.core.files.base import ContentFile
from django.db import transaction
from django.core.exceptions import ValidationError

from .file_processor_service import MangaFileProcessorService
from ..models import Volume, Capitulo
from ..constants import (
    ALLOWED_IMAGE_EXTENSIONS, 
    ALLOWED_ARCHIVE_EXTENSIONS,
    MAX_ARCHIVE_SIZE,
    MESSAGES
)

logger = logging.getLogger(__name__)

class VolumeProcessorService:
    """
    Serviço para processamento de arquivos compactados contendo volumes de mangá.
    
    Este serviço lida com o upload de arquivos compactados contendo múltiplos
    capítulos organizados em pastas, criando automaticamente os registros
    de Volume, Capítulo e Páginas no banco de dados.
    """
    
    def __init__(self, file_processor: MangaFileProcessorService = None):
        """
        Inicializa o serviço com um processador de arquivos opcional.
        
        Args:
            file_processor: Instância de MangaFileProcessorService para processar 
                          arquivos de capítulo individuais. Se não fornecido, 
                          uma nova instância será criada.
        """
        self.file_processor = file_processor or MangaFileProcessorService()
    
    def process_volume_archive(self, volume: Volume, archive_file) -> Tuple[bool, str]:
        """
        Processa um arquivo compactado contendo capítulos de um volume.
        
        Args:
            volume: Instância do Volume ao qual os capítulos serão associados
            archive_file: Arquivo compactado contendo as pastas dos capítulos
            
        Returns:
            Tupla (success, message) indicando o resultado da operação
        """
        logger.info(f"Iniciando processamento de arquivo para o volume {volume.id} - {volume}")
        
        try:
            # Validações iniciais
            if not volume or not hasattr(volume, 'pk'):
                error_msg = "Volume inválido ou não salvo no banco de dados."
                logger.error(error_msg)
                return False, error_msg
                
            # Verifica se o arquivo foi fornecido
            if not archive_file:
                error_msg = "Nenhum arquivo foi fornecido para processamento."
                logger.error(error_msg)
                return False, error_msg
                
            # Cria um diretório temporário para extração
            with tempfile.TemporaryDirectory(prefix=f'manga_volume_{volume.id}_') as temp_dir:
                logger.debug(f"Diretório temporário criado: {temp_dir}")
                
                try:
                    # Extrai o arquivo compactado
                    logger.info("Iniciando extração do arquivo compactado...")
                    extracted_files = self._extract_archive(archive_file, temp_dir)
                    
                    if not extracted_files:
                        error_msg = "Falha ao extrair o arquivo compactado ou arquivo vazio."
                        logger.error(error_msg)
                        return False, error_msg
                    
                    logger.info(f"Arquivo extraído com sucesso. {len(extracted_files)} pastas de capítulos encontradas.")
                    
                    # Processa os capítulos encontrados
                    logger.info("Iniciando processamento dos capítulos...")
                    success, message = self._process_chapters(volume, temp_dir, extracted_files)
                    
                    if success:
                        logger.info(f"Processamento concluído com sucesso: {message}")
                    else:
                        logger.warning(f"Processamento concluído com avisos: {message}")
                    
                    return success, message
                    
                except Exception as e:
                    error_msg = f"Erro durante o processamento: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    return False, error_msg
                
        except Exception as e:
            error_msg = f"Erro inesperado ao processar arquivo de volume: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg
    
    def _extract_archive(self, archive_file, extract_dir: str) -> Dict[str, List[str]]:
        """
        Extrai o arquivo compactado para um diretório temporário.
        
        Args:
            archive_file: Arquivo compactado a ser extraído
            extract_dir: Diretório de destino para extração
            
        Returns:
            Dicionário com a estrutura de pastas/arquivos extraídos
            
        Raises:
            ValidationError: Se o arquivo não for um formato suportado
        """
        from pathlib import Path
        
        # Estrutura para armazenar os arquivos extraídos
        extracted_files = {}
        
        # Obtém o nome do arquivo para logging
        file_name = getattr(archive_file, 'name', 'arquivo_desconhecido')
        logger.info(f"Iniciando extração do arquivo: {file_name}")
        
        # Verifica se o arquivo tem uma extensão suportada
        file_name_lower = file_name.lower()
        supported_extensions = ['.zip', '.rar', '.7z', '.cbz', '.cbr', '.cb7']
        if not any(file_name_lower.endswith(ext) for ext in supported_extensions):
            error_msg = f"Formato de arquivo não suportado: {file_name}. Formatos suportados: {', '.join(supported_extensions)}"
            logger.error(error_msg)
            raise ValidationError(error_msg)
        
        # Verifica o tamanho do arquivo
        try:
            file_size = archive_file.size if hasattr(archive_file, 'size') else os.path.getsize(archive_file)
            if file_size > MAX_ARCHIVE_SIZE:
                error_msg = f"Arquivo muito grande. Tamanho máximo permitido: {MAX_ARCHIVE_SIZE/1024/1024:.2f}MB"
                logger.error(error_msg)
                raise ValidationError(error_msg)
        except (AttributeError, OSError) as e:
            logger.warning(f"Não foi possível verificar o tamanho do arquivo: {str(e)}")
        
        # Tenta importar as bibliotecas necessárias
        try:
            import zipfile
            import rarfile
            import py7zr
        except ImportError as e:
            error_msg = f"Erro ao importar bibliotecas necessárias: {str(e)}"
            logger.error(error_msg)
            raise ImportError("Bibliotecas necessárias não encontradas. Certifique-se de que todas as dependências estão instaladas.")
        
        try:
            # Salva o arquivo temporariamente se for um InMemoryUploadedFile
            temp_path = os.path.join(extract_dir, 'temp_archive')
            with open(temp_path, 'wb+') as temp_file:
                for chunk in archive_file.chunks():
                    temp_file.write(chunk)
            
            # Processa o arquivo com base na extensão
            if file_name.endswith('.zip'):
                with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                    # Extrai todos os arquivos
                    zip_ref.extractall(extract_dir)
                    
                    # Mapeia a estrutura de diretórios
                    for file_path in zip_ref.namelist():
                        self._add_to_file_structure(extracted_files, file_path)
                        
            elif file_name.endswith('.rar') and rarfile:
                with rarfile.RarFile(temp_path, 'r') as rar_ref:
                    # Extrai todos os arquivos
                    rar_ref.extractall(extract_dir)
                    
                    # Mapeia a estrutura de diretórios
                    for file_path in rar_ref.namelist():
                        self._add_to_file_structure(extracted_files, file_path)
                        
            elif file_name.endswith('.7z') and py7zr:
                with py7zr.SevenZipFile(temp_path, 'r') as seven_zip_ref:
                    # Extrai todos os arquivos
                    seven_zip_ref.extractall(extract_dir)
                    
                    # Mapeia a estrutura de diretórios
                    for file_path in seven_zip_ref.getnames():
                        self._add_to_file_structure(extracted_files, file_path)
                        
            else:
                raise ValidationError("Formato de arquivo não suportado. Use ZIP, RAR ou 7Z.")
            
            # Remove o arquivo temporário
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
            return extracted_files
            
        except Exception as e:
            logger.error(f"Erro ao extrair arquivo: {str(e)}", exc_info=True)
            raise ValidationError(f"Erro ao extrair o arquivo: {str(e)}")
    
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
