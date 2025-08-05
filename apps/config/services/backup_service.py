"""Serviço especializado para operações de backup e restauração

Este módulo fornece funcionalidades completas para:
- Criação de backups (banco de dados, mídia, configurações)
- Restauração de backups com validação de integridade
- Gerenciamento de metadados e auditoria
- Validação de segurança e integridade de arquivos
- Estatísticas e limpeza automática de backups antigos
- Logging estruturado para auditoria completa

Versão: 2.0
Autor: Sistema de Backup Project Nix
Data: 2024
"""

import hashlib
import json
import logging
import os
import shutil
import subprocess
import tarfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.config.interfaces.services import IBackupService
from apps.config.models import DatabaseConfiguration, UserActivityLog
from apps.config.models.backup_models import BackupMetadata

User = get_user_model()
logger = logging.getLogger(__name__)


class BackupService(IBackupService):
    """Serviço para operações de backup e restauração seguindo princípios SOLID
    
    Este serviço implementa:
    - Padrão Strategy para diferentes tipos de backup
    - Validação robusta de integridade
    - Logging estruturado para auditoria
    - Tratamento de erros com rollback automático
    """
    
    # Constantes de configuração
    MAX_BACKUP_SIZE = 500 * 1024 * 1024  # 500MB
    ALLOWED_EXTENSIONS = {'.backup', '.sql', '.sqlite3', '.tar.gz', '.json'}
    HASH_ALGORITHM = 'sha256'
    
    def __init__(self):
        """Inicializa o serviço de backup com configurações padrão"""
        self.backup_base_dir = Path(settings.BASE_DIR) / 'backups'
        self.database_backup_dir = self.backup_base_dir / 'database'
        self.media_backup_dir = self.backup_base_dir / 'media'
        self.config_backup_dir = self.backup_base_dir / 'configurations'
        
        # Criar diretórios se não existirem
        self._ensure_backup_directories()
    
    def _ensure_backup_directories(self) -> None:
        """Garante que os diretórios de backup existam com permissões adequadas"""
        directories = [
            self.database_backup_dir,
            self.media_backup_dir,
            self.config_backup_dir
        ]
        
        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                # Verificar se o diretório é gravável
                if not os.access(directory, os.W_OK):
                    logger.warning(f"Diretório {directory} não é gravável")
            except OSError as e:
                logger.error(f"Erro ao criar diretório {directory}: {e}")
                raise ValidationError(f"Não foi possível criar diretório de backup: {e}")
    
    def create_database_backup(self, user: Optional[User] = None, description: str = "") -> Tuple[bool, str, Optional[str]]:
        """Cria backup do banco de dados com validação e registro completo
        
        Args:
            user: Usuário que está criando o backup
            description: Descrição personalizada do backup
            
        Returns:
            Tuple[bool, str, Optional[str]]: (sucesso, mensagem, caminho_arquivo)
        """
        backup_path = None
        backup_metadata = None
        
        try:
            logger.info(f"Iniciando criação de backup de banco de dados por {user or 'sistema'}")
            
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f'database_backup_{timestamp}.sql'
            backup_path = self.database_backup_dir / backup_filename
            
            # Validar espaço em disco disponível
            if not self._check_disk_space(self.database_backup_dir):
                return False, 'Espaço em disco insuficiente para criar backup', None
            
            # Criar registro inicial no banco
            backup_metadata = BackupMetadata.objects.create(
                name=f'Backup BD {timestamp}',
                backup_type='database',
                status='in_progress',
                file_path=str(backup_path),
                created_by=user,
                description=description or f'Backup automático criado em {timezone.now().strftime("%d/%m/%Y às %H:%M")}'
            )
            
            # Executar backup
            backup_success = self._execute_database_backup(backup_path)
            
            if backup_success and backup_path.exists():
                # Validar tamanho do arquivo
                file_size = backup_path.stat().st_size
                if file_size > self.MAX_BACKUP_SIZE:
                    logger.warning(f"Backup muito grande: {file_size} bytes")
                
                # Gerar hash SHA256
                sha256_hash = self._generate_file_hash(backup_path)
                
                # Atualizar registro no banco de dados
                backup_metadata.status = 'completed'
                backup_metadata.file_size = file_size
                backup_metadata.sha256_hash = sha256_hash
                backup_metadata.save()
                
                # Salvar metadados em arquivo também
                self._save_backup_metadata(backup_path, sha256_hash, 'database', user)
                
                self._log_backup_activity('database_backup_created', user, f'Backup criado: {backup_metadata.slug}')
                
                logger.info(f"Backup de banco criado com sucesso: {backup_filename}")
                return True, f'Backup criado com sucesso: {backup_filename}', str(backup_path)
            else:
                # Falha no backup - limpar recursos
                if backup_metadata:
                    backup_metadata.status = 'failed'
                    backup_metadata.save()
                
                self._cleanup_failed_backup(backup_path)
                logger.error("Falha ao executar backup do banco de dados")
                return False, 'Falha ao criar backup do banco de dados', None
                
        except Exception as e:
            logger.error(f"Erro ao criar backup de banco: {e}")
            
            # Limpar recursos em caso de erro
            if backup_metadata:
                backup_metadata.status = 'failed'
                backup_metadata.save()
            
            self._cleanup_failed_backup(backup_path)
            return False, f'Erro ao criar backup: {str(e)}', None
    
    def get_backup_by_slug(self, slug: str) -> Optional[BackupMetadata]:
        """Obtém backup pelo slug com validação
        
        Args:
            slug: Identificador único do backup
            
        Returns:
            BackupMetadata ou None se não encontrado
        """
        try:
            if not slug or not isinstance(slug, str):
                logger.warning(f"Slug inválido fornecido: {slug}")
                return None
                
            return BackupMetadata.objects.get(slug=slug)
        except BackupMetadata.DoesNotExist:
            logger.info(f"Backup não encontrado para slug: {slug}")
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar backup por slug {slug}: {e}")
            return None
    
    def verify_backup_integrity(self, file_path: str) -> Dict[str, Any]:
        """Verifica integridade completa de um backup
        
        Args:
            file_path: Caminho para o arquivo de backup
            
        Returns:
            Dict com informações de validação
        """
        try:
            backup_file = Path(file_path)
            
            # Validações básicas
            if not backup_file.exists():
                return {
                    'valid': False, 
                    'error': 'Arquivo não encontrado',
                    'checks': {'file_exists': False}
                }
            
            if backup_file.stat().st_size == 0:
                return {
                    'valid': False, 
                    'error': 'Arquivo vazio',
                    'checks': {'file_exists': True, 'file_size': False}
                }
            
            checks = {
                'file_exists': True,
                'file_size': True,
                'extension_valid': backup_file.suffix in self.ALLOWED_EXTENSIONS,
                'size_within_limits': backup_file.stat().st_size <= self.MAX_BACKUP_SIZE
            }
            
            # Verificar hash se disponível no banco de dados
            try:
                backup_metadata = BackupMetadata.objects.get(file_path=file_path)
                if backup_metadata.sha256_hash:
                    current_hash = self._generate_file_hash(backup_file)
                    if current_hash != backup_metadata.sha256_hash:
                        return {'valid': False, 'error': 'Hash SHA256 não confere'}
            except BackupMetadata.DoesNotExist:
                # Se não há registro no banco, verificar arquivo de metadados
                metadata_file = backup_file.with_suffix('.metadata.json')
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        stored_hash = metadata.get('sha256')
                        if stored_hash:
                            current_hash = self._generate_file_hash(backup_file)
                            if current_hash != stored_hash:
                                return {'valid': False, 'error': 'Hash SHA256 não confere (arquivo de metadados)'}
                    except Exception:
                        pass
            
            return {'valid': True, 'message': 'Backup íntegro'}
            
        except Exception as e:
            return {'valid': False, 'error': f'Erro na verificação: {str(e)}'}
    
    def create_media_backup(self, user: Optional[User] = None, description: str = "") -> Tuple[bool, str, Optional[str]]:
        """Cria backup dos arquivos de mídia com validação robusta
        
        Args:
            user: Usuário que está criando o backup
            description: Descrição personalizada do backup
            
        Returns:
            Tuple[bool, str, Optional[str]]: (sucesso, mensagem, caminho_arquivo)
        """
        backup_path = None
        backup_metadata = None
        
        try:
            logger.info(f"Iniciando criação de backup de mídia por {user or 'sistema'}")
            
            # Verificar se o diretório de mídia existe e não está vazio
            media_root = Path(settings.MEDIA_ROOT)
            if not media_root.exists():
                logger.warning("Diretório de mídia não existe")
                return False, 'Diretório de mídia não existe', None
            
            # Contar arquivos válidos (excluindo temporários)
            valid_files = [
                f for f in media_root.rglob('*') 
                if f.is_file() and not any(pattern in str(f) for pattern in ['.tmp', '__pycache__', '.cache'])
            ]
            
            if not valid_files:
                logger.info("Diretório de mídia está vazio")
                return False, 'Diretório de mídia vazio', None
            
            # Validar espaço em disco
            if not self._check_disk_space(self.media_backup_dir, 200):  # 200MB para mídia
                return False, 'Espaço em disco insuficiente para backup de mídia', None
            
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f'media_backup_{timestamp}.tar.gz'
            backup_path = self.media_backup_dir / backup_filename
            
            # Criar registro inicial no banco
            backup_metadata = BackupMetadata.objects.create(
                name=f'Backup Mídia {timestamp}',
                backup_type='media',
                status='in_progress',
                file_path=str(backup_path),
                created_by=user,
                description=description or f'Backup de mídia criado em {timezone.now().strftime("%d/%m/%Y às %H:%M")}'
            )
            
            logger.info(f"Criando arquivo tar.gz com {len(valid_files)} arquivos")
            
            # Criar arquivo tar.gz com compressão otimizada
            with tarfile.open(backup_path, 'w:gz', compresslevel=6) as tar:
                # Filtrar arquivos temporários e de cache
                def filter_func(tarinfo):
                    if any(pattern in tarinfo.name for pattern in ['.tmp', '__pycache__', '.cache']):
                        return None
                    return tarinfo
                
                tar.add(media_root, arcname='media', filter=filter_func)
            
            if not backup_path.exists() or backup_path.stat().st_size == 0:
                logger.error("Arquivo de backup não foi criado ou está vazio")
                raise Exception("Falha na criação do arquivo de backup")
            
            # Validar tamanho do arquivo
            file_size = backup_path.stat().st_size
            if file_size > self.MAX_BACKUP_SIZE:
                logger.warning(f"Backup de mídia muito grande: {file_size} bytes")
            
            # Gerar hash SHA256
            sha256_hash = self._generate_file_hash(backup_path)
            
            # Atualizar registro no banco de dados
            backup_metadata.status = 'completed'
            backup_metadata.file_size = file_size
            backup_metadata.sha256_hash = sha256_hash
            backup_metadata.save()
            
            # Salvar metadados em arquivo
            self._save_backup_metadata(backup_path, sha256_hash, 'media', user)
            
            self._log_backup_activity('media_backup_created', user, f'Backup criado: {backup_metadata.slug}')
            
            logger.info(f"Backup de mídia criado com sucesso: {backup_filename}")
            return True, f'Backup de mídia criado: {backup_filename}', str(backup_path)
            
        except Exception as e:
            logger.error(f"Erro ao criar backup de mídia: {e}")
            
            # Limpar recursos em caso de erro
            if backup_metadata:
                backup_metadata.status = 'failed'
                backup_metadata.save()
            
            self._cleanup_failed_backup(backup_path)
            return False, f'Erro ao criar backup de mídia: {str(e)}', None
    
    def create_configuration_backup(self, user: Optional[User] = None, description: str = "") -> Tuple[bool, str, Optional[str]]:
        """Cria backup das configurações do sistema com validação robusta
        
        Args:
            user: Usuário que está criando o backup
            description: Descrição personalizada do backup
            
        Returns:
            Tuple[bool, str, Optional[str]]: (sucesso, mensagem, caminho_arquivo)
        """
        backup_path = None
        backup_metadata = None
        
        try:
            logger.info(f"Iniciando criação de backup de configurações por {user or 'sistema'}")
            
            # Validar espaço em disco
            if not self._check_disk_space(self.config_backup_dir, 10):  # 10MB para configurações
                return False, 'Espaço em disco insuficiente para backup de configurações', None
            
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f'config_backup_{timestamp}.json'
            backup_path = self.config_backup_dir / backup_filename
            
            # Criar registro inicial no banco
            backup_metadata = BackupMetadata.objects.create(
                name=f'Backup Config {timestamp}',
                backup_type='configuration',
                status='in_progress',
                file_path=str(backup_path),
                created_by=user,
                description=description or f'Backup de configurações criado em {timezone.now().strftime("%d/%m/%Y às %H:%M")}'
            )
            
            logger.info("Coletando configurações do sistema")
            
            # Coletar configurações
            configurations = self._collect_system_configurations()
            
            if not configurations:
                logger.warning("Nenhuma configuração encontrada para backup")
                raise Exception("Nenhuma configuração disponível para backup")
            
            logger.info(f"Salvando {len(configurations)} configurações em arquivo JSON")
            
            # Salvar em arquivo JSON
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(configurations, f, indent=2, ensure_ascii=False, default=str)
            
            if not backup_path.exists() or backup_path.stat().st_size == 0:
                logger.error("Arquivo de backup não foi criado ou está vazio")
                raise Exception("Falha na criação do arquivo de backup")
            
            # Validar tamanho do arquivo
            file_size = backup_path.stat().st_size
            
            # Gerar hash SHA256
            sha256_hash = self._generate_file_hash(backup_path)
            
            # Atualizar registro no banco de dados
            backup_metadata.status = 'completed'
            backup_metadata.file_size = file_size
            backup_metadata.sha256_hash = sha256_hash
            backup_metadata.save()
            
            # Salvar metadados em arquivo
            self._save_backup_metadata(backup_path, sha256_hash, 'configuration', user)
            
            self._log_backup_activity('config_backup_created', user, f'Backup criado: {backup_metadata.slug}')
            
            logger.info(f"Backup de configurações criado com sucesso: {backup_filename}")
            return True, f'Backup de configurações criado: {backup_filename}', str(backup_path)
            
        except Exception as e:
            logger.error(f"Erro ao criar backup de configurações: {e}")
            
            # Limpar recursos em caso de erro
            if backup_metadata:
                backup_metadata.status = 'failed'
                backup_metadata.save()
            
            self._cleanup_failed_backup(backup_path)
            return False, f'Erro ao criar backup de configurações: {str(e)}', None
    
    def restore_database_backup(self, backup_path: str, user: Optional[User] = None) -> Tuple[bool, str]:
        """Restaura backup do banco de dados com validação robusta
        
        Args:
            backup_path: Caminho para o arquivo de backup
            user: Usuário executando a restauração
            
        Returns:
            Tuple[bool, str]: (sucesso, mensagem)
        """
        try:
            logger.info(f"Iniciando restauração de banco de dados por {user or 'sistema'}: {backup_path}")
            
            backup_file = Path(backup_path)
            
            # Validar arquivo de backup
            is_valid, error_msg = self._validate_backup_file(backup_file)
            if not is_valid:
                logger.error(f"Arquivo de backup inválido: {error_msg}")
                return False, f'Arquivo de backup inválido: {error_msg}'
            
            # Validar integridade do arquivo
            integrity_result = self.verify_backup_integrity(backup_path)
            if not integrity_result['valid']:
                logger.error(f"Backup corrompido: {integrity_result.get('error', 'Erro desconhecido')}")
                return False, f'Arquivo de backup corrompido: {integrity_result.get("error", "Erro desconhecido")}'
            
            # Tentar criar backup automático antes da restauração
            try:
                logger.info("Criando backup automático antes da restauração")
                auto_backup_success, auto_backup_msg, _ = self.create_database_backup(
                    user, "Backup automático antes da restauração"
                )
                if auto_backup_success:
                    logger.info("Backup automático criado com sucesso")
                    self._log_backup_activity('auto_backup_before_restore', user, f'Backup automático criado antes da restauração: {auto_backup_msg}')
                else:
                    logger.warning(f"Falha no backup automático: {auto_backup_msg}")
            except Exception as e:
                logger.warning(f"Erro no backup automático: {e}")
                self._log_backup_activity('auto_backup_failed', user, f'Falha ao criar backup automático: {str(e)}')
            
            # Executar restauração
            logger.info("Executando restauração do banco de dados")
            success = self._execute_database_restore(backup_file)
            
            if success:
                logger.info(f"Banco de dados restaurado com sucesso de: {backup_path}")
                self._log_backup_activity('database_restore', user, f'Restaurado de {backup_file.name}')
                return True, 'Banco de dados restaurado com sucesso'
            else:
                logger.error(f"Falha ao restaurar banco de dados de: {backup_path}")
                return False, 'Falha ao restaurar banco de dados'
                
        except Exception as e:
            logger.error(f"Erro ao restaurar backup: {e}")
            return False, f'Erro ao restaurar backup: {str(e)}'
    
    def restore_media_backup(self, backup_path: str, user: Optional[User] = None) -> Tuple[bool, str]:
        """Restaura backup dos arquivos de mídia com validação de segurança
        
        Args:
            backup_path: Caminho para o arquivo de backup
            user: Usuário executando a restauração
            
        Returns:
            Tuple[bool, str]: (sucesso, mensagem)
        """
        try:
            logger.info(f"Iniciando restauração de mídia por {user or 'sistema'}: {backup_path}")
            
            backup_file = Path(backup_path)
            
            # Validar arquivo de backup
            is_valid, error_msg = self._validate_backup_file(backup_file)
            if not is_valid:
                logger.error(f"Arquivo de backup inválido: {error_msg}")
                return False, f'Arquivo de backup inválido: {error_msg}'
            
            # Validar se é um arquivo tar.gz válido
            if not tarfile.is_tarfile(backup_file):
                logger.error(f"Arquivo não é um tar.gz válido: {backup_path}")
                return False, 'Arquivo de backup inválido'
            
            # Tentar criar backup automático antes da restauração
            try:
                logger.info("Criando backup automático de mídia antes da restauração")
                auto_backup_success, auto_backup_msg, _ = self.create_media_backup(
                    user, "Backup automático antes da restauração"
                )
                if auto_backup_success:
                    logger.info("Backup automático de mídia criado com sucesso")
                    self._log_backup_activity('auto_backup_before_restore', user, f'Backup automático criado antes da restauração: {auto_backup_msg}')
                else:
                    logger.warning(f"Falha no backup automático de mídia: {auto_backup_msg}")
            except Exception as e:
                logger.warning(f"Erro no backup automático de mídia: {e}")
                self._log_backup_activity('auto_backup_failed', user, f'Falha ao criar backup automático: {str(e)}')
            
            # Extrair arquivos com validação de segurança
            media_root = Path(settings.MEDIA_ROOT)
            
            logger.info("Validando segurança do arquivo tar.gz")
            with tarfile.open(backup_file, 'r:gz') as tar:
                # Validar membros do arquivo antes da extração
                for member in tar.getmembers():
                    if member.name.startswith('/') or '..' in member.name:
                        logger.error(f"Caminho inseguro detectado: {member.name}")
                        return False, f'Arquivo de backup contém caminhos inseguros: {member.name}'
                
                # Extrair com segurança
                logger.info("Extraindo arquivos de mídia")
                tar.extractall(path=media_root.parent, members=tar.getmembers())
            
            logger.info(f"Mídia restaurada com sucesso de: {backup_path}")
            self._log_backup_activity('media_restore', user, f'Restaurado de {backup_file.name}')
            return True, 'Arquivos de mídia restaurados com sucesso'
            
        except Exception as e:
            logger.error(f"Erro ao restaurar mídia: {e}")
            return False, f'Erro ao restaurar mídia: {str(e)}'
    
    def restore_configuration_backup(self, backup_path: str, user: Optional[User] = None) -> Tuple[bool, str]:
        """Restaura backup das configurações com validação robusta
        
        Args:
            backup_path: Caminho para o arquivo de backup
            user: Usuário executando a restauração
            
        Returns:
            Tuple[bool, str]: (sucesso, mensagem)
        """
        try:
            logger.info(f"Iniciando restauração de configurações por {user or 'sistema'}: {backup_path}")
            
            backup_file = Path(backup_path)
            
            # Validar arquivo de backup
            is_valid, error_msg = self._validate_backup_file(backup_file)
            if not is_valid:
                logger.error(f"Arquivo de backup inválido: {error_msg}")
                return False, f'Arquivo de backup inválido: {error_msg}'
            
            # Ler e validar JSON
            logger.info("Lendo arquivo de configurações")
            with open(backup_file, 'r', encoding='utf-8') as f:
                configurations = json.load(f)
            
            # Validar estrutura do backup
            if not self._validate_configuration_backup(configurations):
                logger.error("Estrutura do backup de configurações inválida")
                return False, 'Estrutura do backup inválida'
            
            # Restaurar configurações
            logger.info("Restaurando configurações")
            restored_count = self._restore_configurations(configurations, user)
            
            logger.info(f"Configurações restauradas com sucesso: {restored_count} itens")
            self._log_backup_activity('config_restore', user, f'Restaurado de {backup_file.name}')
            return True, f'Restauradas {restored_count} configurações com sucesso'
            
        except json.JSONDecodeError as e:
            logger.error(f"Erro de formato JSON: {e}")
            return False, 'Arquivo de backup com formato JSON inválido'
        except Exception as e:
            logger.error(f"Erro ao restaurar configurações: {e}")
            return False, f'Erro ao restaurar configurações: {str(e)}'
    
    def list_backups(self, backup_type: str = 'all') -> List[Dict[str, Any]]:
        """Lista backups disponíveis com informações detalhadas
        
        Args:
            backup_type: Tipo de backup ('database', 'media', 'configuration', 'all')
            
        Returns:
            Lista de dicionários com informações dos backups
        """
        try:
            logger.debug(f"Listando backups do tipo: {backup_type}")
            
            backup_types = {
                'database': self.database_backup_dir,
                'media': self.media_backup_dir,
                'configuration': self.config_backup_dir,
                'all': None
            }
            
            if backup_type not in backup_types:
                logger.warning(f"Tipo de backup inválido: {backup_type}")
                return []
            
            backups = []
            
            if backup_type == 'all':
                # Listar todos os tipos
                for btype, directory in backup_types.items():
                    if btype != 'all' and directory:
                        backups.extend(self._get_backups_from_directory(directory, btype))
            else:
                directory = backup_types[backup_type]
                if directory and directory.exists():
                    backups = self._get_backups_from_directory(directory, backup_type)
            
            # Ordenar por data de criação (mais recente primeiro)
            sorted_backups = sorted(backups, key=lambda x: x['created'], reverse=True)
            
            logger.debug(f"Encontrados {len(sorted_backups)} backups")
            return sorted_backups
            
        except Exception as e:
            logger.error(f"Erro ao listar backups: {e}")
            return []
    
    def _get_backups_from_directory(self, directory: Path, backup_type: str) -> List[Dict[str, Any]]:
        """Obtém lista de backups de um diretório específico
        
        Args:
            directory: Diretório para buscar backups
            backup_type: Tipo de backup
            
        Returns:
            Lista de informações dos backups
        """
        backups = []
        
        try:
            if not directory.exists():
                return backups
            
            for backup_file in directory.glob('*'):
                if backup_file.is_file() and backup_file.suffix in self.ALLOWED_EXTENSIONS:
                    try:
                        # Buscar metadados no banco de dados
                        backup_metadata = None
                        try:
                            backup_metadata = BackupMetadata.objects.get(file_path=str(backup_file))
                        except BackupMetadata.DoesNotExist:
                            pass
                        
                        backup_info = {
                            'type': backup_type,
                            'filename': backup_file.name,
                            'path': str(backup_file),
                            'size': backup_file.stat().st_size,
                            'size_human': self._format_file_size(backup_file.stat().st_size),
                            'created': timezone.datetime.fromtimestamp(backup_file.stat().st_mtime),
                            'extension': backup_file.suffix,
                            'metadata': None
                        }
                        
                        # Adicionar informações do banco se disponível
                        if backup_metadata:
                            backup_info.update({
                                'slug': backup_metadata.slug,
                                'name': backup_metadata.name,
                                'status': backup_metadata.status,
                                'description': backup_metadata.description,
                                'created_by': backup_metadata.created_by.username if backup_metadata.created_by else None,
                                'sha256_hash': backup_metadata.sha256_hash
                            })
                        
                        backups.append(backup_info)
                        
                    except Exception as e:
                        logger.warning(f"Erro ao processar backup {backup_file}: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Erro ao listar backups do diretório {directory}: {e}")
        
        return backups
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Formata tamanho do arquivo em formato legível
        
        Args:
            size_bytes: Tamanho em bytes
            
        Returns:
            String formatada (ex: '1.5 MB')
        """
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"
    
    def delete_backup(self, backup_path: str, user: Optional[User] = None) -> Tuple[bool, str]:
        """Remove um backup específico com validação de segurança
        
        Args:
            backup_path: Caminho do arquivo de backup
            user: Usuário executando a operação
            
        Returns:
            Tuple[bool, str]: (sucesso, mensagem)
        """
        try:
            logger.info(f"Removendo backup por {user or 'sistema'}: {backup_path}")
            
            backup_file = Path(backup_path)
            
            # Validar se o arquivo está dentro dos diretórios de backup
            if not self._is_safe_backup_path(backup_file):
                logger.error(f"Caminho de backup inseguro: {backup_path}")
                return False, 'Caminho de backup inválido ou inseguro'
            
            if not backup_file.exists():
                logger.warning(f"Arquivo de backup não encontrado: {backup_path}")
                return False, 'Arquivo de backup não encontrado'
            
            # Remover registro do banco de dados se existir
            try:
                backup_metadata = BackupMetadata.objects.get(file_path=backup_path)
                backup_metadata.delete()
                logger.info(f"Metadados do backup removidos: {backup_metadata.slug}")
            except BackupMetadata.DoesNotExist:
                logger.debug("Nenhum metadado encontrado no banco para este backup")
            
            # Remover arquivo físico
            backup_file.unlink()
            
            # Remover arquivo de metadados se existir
            metadata_file = backup_file.with_suffix('.metadata.json')
            if metadata_file.exists():
                metadata_file.unlink()
                logger.debug("Arquivo de metadados removido")
            
            self._log_backup_activity('backup_deleted', user, f'Backup removido: {backup_file.name}')
            
            logger.info(f"Backup removido com sucesso: {backup_file.name}")
            return True, f'Backup {backup_file.name} removido com sucesso'
                
        except Exception as e:
            logger.error(f"Erro ao remover backup: {e}")
            return False, f'Erro ao remover backup: {str(e)}'
    
    def _execute_database_backup(self, backup_path: Path) -> bool:
        """Executa o backup do banco baseado no engine configurado automaticamente"""
        try:
            # Obter configuração do banco de dados padrão
            db_config = settings.DATABASES['default']
            engine = db_config['ENGINE']
            
            if engine == 'django.db.backends.sqlite3':
                # Backup para SQLite - cópia direta do arquivo
                db_file = Path(db_config['NAME'])
                if db_file.exists():
                    shutil.copy2(db_file, backup_path)
                    return True
                else:
                    # Se o arquivo não existe, cria um backup vazio
                    backup_path.touch()
                    return False
                    
            elif engine == 'django.db.backends.postgresql':
                # Backup para PostgreSQL usando pg_dump
                cmd = [
                    'pg_dump',
                    '--host', db_config.get('HOST', 'localhost'),
                    '--port', str(db_config.get('PORT', 5432)),
                    '--username', db_config.get('USER', ''),
                    '--dbname', db_config.get('NAME', ''),
                    '--file', str(backup_path),
                    '--verbose',
                    '--no-password'
                ]
                
                # Configurar variáveis de ambiente para autenticação
                env = os.environ.copy()
                if db_config.get('PASSWORD'):
                    env['PGPASSWORD'] = db_config['PASSWORD']
                
                result = subprocess.run(cmd, env=env, capture_output=True, text=True)
                return result.returncode == 0
                
            elif engine == 'django.db.backends.mysql':
                # Backup para MySQL usando mysqldump
                cmd = [
                    'mysqldump',
                    '--host', db_config.get('HOST', 'localhost'),
                    '--port', str(db_config.get('PORT', 3306)),
                    '--user', db_config.get('USER', ''),
                    '--single-transaction',
                    '--routines',
                    '--triggers',
                    db_config.get('NAME', '')
                ]
                
                if db_config.get('PASSWORD'):
                    cmd.append(f'--password={db_config["PASSWORD"]}')
                
                with open(backup_path, 'w') as f:
                    result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
                
                return result.returncode == 0
                
            else:
                # Engine não suportado - cria arquivo vazio para evitar erro
                backup_path.touch()
                return False
                
        except Exception as e:
            # Em caso de erro, cria um arquivo vazio para evitar IntegrityError
            try:
                backup_path.touch()
            except:
                pass
            return False
    
    def _execute_database_restore(self, backup_file: Path) -> bool:
        """Executa a restauração do banco baseado no engine configurado automaticamente"""
        try:
            # Obter configuração do banco de dados padrão
            db_config = settings.DATABASES['default']
            engine = db_config['ENGINE']
            
            if engine == 'django.db.backends.sqlite3':
                # Restauração para SQLite - cópia direta do arquivo
                db_file = Path(db_config['NAME'])
                if backup_file.exists():
                    shutil.copy2(backup_file, db_file)
                    return True
                return False
                
            elif engine == 'django.db.backends.postgresql':
                # Restauração para PostgreSQL usando psql
                cmd = [
                    'psql',
                    '--host', db_config.get('HOST', 'localhost'),
                    '--port', str(db_config.get('PORT', 5432)),
                    '--username', db_config.get('USER', ''),
                    '--dbname', db_config.get('NAME', ''),
                    '--file', str(backup_file),
                    '--quiet'
                ]
                
                # Configurar variáveis de ambiente para autenticação
                env = os.environ.copy()
                if db_config.get('PASSWORD'):
                    env['PGPASSWORD'] = db_config['PASSWORD']
                
                result = subprocess.run(cmd, env=env, capture_output=True, text=True)
                return result.returncode == 0
                
            elif engine == 'django.db.backends.mysql':
                # Restauração para MySQL usando mysql
                cmd = [
                    'mysql',
                    '--host', db_config.get('HOST', 'localhost'),
                    '--port', str(db_config.get('PORT', 3306)),
                    '--user', db_config.get('USER', ''),
                    db_config.get('NAME', '')
                ]
                
                if db_config.get('PASSWORD'):
                    cmd.append(f'--password={db_config["PASSWORD"]}')
                
                with open(backup_file, 'r') as f:
                    result = subprocess.run(cmd, stdin=f, capture_output=True, text=True)
                
                return result.returncode == 0
                
            else:
                # Engine não suportado
                return False
                
        except Exception as e:
            return False
    
    def _generate_file_hash(self, file_path: Path) -> str:
        """Gera hash SHA256 de um arquivo para verificação de integridade
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Hash SHA256 em hexadecimal
        """
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                # Ler arquivo em blocos para eficiência de memória
                for byte_block in iter(lambda: f.read(8192), b""):
                    sha256_hash.update(byte_block)
            
            hash_value = sha256_hash.hexdigest()
            logger.debug(f"Hash SHA256 gerado para {file_path.name}: {hash_value[:16]}...")
            return hash_value
            
        except Exception as e:
            logger.error(f"Erro ao gerar hash do arquivo {file_path}: {e}")
            return ""
    
    def _save_backup_metadata(self, backup_path: Path, sha256_hash: str, backup_type: str, user: Optional[User]) -> None:
        """Salva metadados do backup em arquivo JSON para redundância
        
        Args:
            backup_path: Caminho do arquivo de backup
            sha256_hash: Hash SHA256 do arquivo
            backup_type: Tipo do backup
            user: Usuário que criou o backup
        """
        try:
            metadata = {
                'filename': backup_path.name,
                'type': backup_type,
                'created_at': timezone.now().isoformat(),
                'created_by': user.username if user else 'system',
                'sha256': sha256_hash,
                'size': backup_path.stat().st_size,
                'version': '1.0',
                'django_version': getattr(settings, 'DJANGO_VERSION', 'unknown'),
                'backup_service_version': '2.0'
            }
            
            metadata_file = backup_path.with_suffix('.metadata.json')
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Metadados salvos: {metadata_file.name}")
            
        except Exception as e:
            logger.warning(f"Erro ao salvar metadados do backup: {e}")
    
    def _validate_backup_integrity(self, backup_file: Path) -> bool:
        """Valida integridade do backup comparando hash e metadados
        
        Args:
            backup_file: Arquivo de backup para validar
            
        Returns:
            True se o backup está íntegro
        """
        try:
            logger.debug(f"Validando integridade do backup: {backup_file.name}")
            
            # Verificar se arquivo existe e não está vazio
            if not backup_file.exists():
                logger.error(f"Arquivo de backup não existe: {backup_file}")
                return False
            
            if backup_file.stat().st_size == 0:
                logger.error(f"Arquivo de backup está vazio: {backup_file}")
                return False
            
            # Verificar metadados do banco de dados primeiro
            try:
                backup_metadata = BackupMetadata.objects.get(file_path=str(backup_file))
                if backup_metadata.sha256_hash:
                    current_hash = self._generate_file_hash(backup_file)
                    if backup_metadata.sha256_hash != current_hash:
                        logger.error(f"Hash SHA256 não confere para {backup_file.name}")
                        return False
                    logger.debug("Hash SHA256 validado com sucesso")
                    return True
            except BackupMetadata.DoesNotExist:
                logger.debug("Metadados não encontrados no banco, verificando arquivo")
            
            # Verificar arquivo de metadados como fallback
            metadata_file = backup_file.with_suffix('.metadata.json')
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    
                    stored_hash = metadata.get('sha256')
                    if stored_hash:
                        current_hash = self._generate_file_hash(backup_file)
                        if stored_hash != current_hash:
                            logger.error(f"Hash do arquivo de metadados não confere para {backup_file.name}")
                            return False
                        logger.debug("Hash do arquivo de metadados validado")
                        return True
                except json.JSONDecodeError:
                    logger.warning(f"Arquivo de metadados corrompido: {metadata_file}")
            
            # Se não há metadados, assumir válido mas registrar aviso
            logger.warning(f"Nenhum metadado encontrado para validação de {backup_file.name}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao validar integridade do backup {backup_file}: {e}")
            return False
    
    def _collect_system_configurations(self) -> Dict[str, Any]:
        """Coleta todas as configurações do sistema"""
        configurations = {
            'timestamp': timezone.now().isoformat(),
            'version': '1.0',
            'database_configurations': [],
            'system_settings': {}
        }
        
        # Coletar configurações de banco
        for config in DatabaseConfiguration.objects.all():
            configurations['database_configurations'].append({
                'name': config.name,
                'description': config.description,
                'engine': config.engine,
                'name_db': config.name_db,
                'host': config.host,
                'port': config.port,
                'user': config.user,
                'options': config.options,
                'is_default': config.is_default,
                'is_active': config.is_active,
                'created_at': config.created_at.isoformat() if config.created_at else None
            })
        
        return configurations
    
    def _validate_configuration_backup(self, configurations: Dict[str, Any]) -> bool:
        """Valida a estrutura de um backup de configurações"""
        required_keys = ['timestamp', 'version']
        return all(key in configurations for key in required_keys)
    
    def _restore_configurations(self, configurations: Dict[str, Any], user: Optional[User]) -> int:
        """Restaura configurações do backup"""
        restored_count = 0
        
        # Restaurar configurações de banco
        for config_data in configurations.get('database_configurations', []):
            try:
                existing = DatabaseConfiguration.objects.filter(
                    name=config_data['name']
                ).first()
                
                if existing:
                    # Atualizar existente
                    for key, value in config_data.items():
                        if key not in ['created_at'] and hasattr(existing, key):
                            setattr(existing, key, value)
                    
                    if user:
                        existing.updated_by = user
                    
                    existing.save()
                else:
                    # Criar novo
                    config = DatabaseConfiguration(
                        created_by=user,
                        updated_by=user,
                        **{k: v for k, v in config_data.items() if k != 'created_at'}
                    )
                    config.save()
                
                restored_count += 1
                
            except Exception as e:
                # Log do erro, mas continua com as outras configurações
                pass
        
        return restored_count
    
    def _get_backup_hash(self, backup_file: Path) -> Optional[str]:
        """Obtém o hash SHA256 de um backup dos metadados"""
        metadata_file = backup_file.with_suffix('.metadata.json')
        
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                return metadata.get('sha256')
            except Exception:
                pass
        
        return None
    
    def _is_safe_backup_path(self, backup_file: Path) -> bool:
        """Verifica se o caminho do backup é seguro (dentro dos diretórios permitidos)"""
        try:
            backup_file_resolved = backup_file.resolve()
            backup_base_resolved = self.backup_base_dir.resolve()
            
            return str(backup_file_resolved).startswith(str(backup_base_resolved))
        except Exception:
            return False
    
    def get_backup_file(self, backup_type: str, filename: str, user: Optional[User] = None) -> Tuple[bool, str, Optional[Path]]:
        """Obtém arquivo de backup para download"""
        try:
            # Determinar diretório baseado no tipo
            if backup_type == 'database':
                backup_dir = self.database_backup_dir
            elif backup_type == 'media':
                backup_dir = self.media_backup_dir
            elif backup_type == 'configurations':
                backup_dir = self.config_backup_dir
            else:
                return False, "Tipo de backup inválido", None
            
            backup_file = backup_dir / filename
            
            # Verificar se o arquivo existe e é seguro
            if not backup_file.exists():
                return False, "Arquivo de backup não encontrado", None
            
            if not self._is_safe_backup_path(backup_file):
                self._log_backup_activity(
                    "DOWNLOAD_BACKUP_SECURITY_VIOLATION",
                    user,
                    f"Tentativa de acesso a arquivo inseguro: {filename}"
                )
                return False, "Acesso negado por motivos de segurança", None
            
            self._log_backup_activity(
                "DOWNLOAD_BACKUP",
                user,
                f"Download do backup {backup_type}: {filename}"
            )
            
            return True, "Arquivo obtido com sucesso", backup_file
            
        except Exception as e:
            error_msg = f"Erro ao obter arquivo de backup: {str(e)}"
            self._log_backup_activity(
                "DOWNLOAD_BACKUP_ERROR",
                user,
                error_msg
            )
            return False, error_msg, None
    
    def _check_disk_space(self, directory: Path, min_space_mb: int = 100) -> bool:
        """Verifica se há espaço em disco suficiente
        
        Args:
            directory: Diretório para verificar espaço
            min_space_mb: Espaço mínimo em MB
            
        Returns:
            True se há espaço suficiente
        """
        try:
            stat = shutil.disk_usage(directory)
            free_space_mb = stat.free / (1024 * 1024)
            
            if free_space_mb < min_space_mb:
                logger.warning(f"Espaço em disco insuficiente: {free_space_mb:.2f}MB disponível, {min_space_mb}MB necessário")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Erro ao verificar espaço em disco: {e}")
            return False
    
    def _cleanup_failed_backup(self, backup_path: Optional[Path]) -> None:
        """Remove arquivos de backup que falharam
        
        Args:
            backup_path: Caminho do arquivo de backup para remover
        """
        if backup_path and backup_path.exists():
            try:
                backup_path.unlink()
                logger.info(f"Arquivo de backup falho removido: {backup_path}")
            except Exception as e:
                logger.error(f"Erro ao remover arquivo de backup falho {backup_path}: {e}")
    
    def _validate_backup_file(self, file_path: Path) -> Tuple[bool, str]:
        """Valida arquivo de backup antes de operações
        
        Args:
            file_path: Caminho do arquivo para validar
            
        Returns:
            Tuple[bool, str]: (válido, mensagem_erro)
        """
        if not file_path.exists():
            return False, "Arquivo não encontrado"
        
        if file_path.stat().st_size == 0:
            return False, "Arquivo está vazio"
        
        if file_path.suffix not in self.ALLOWED_EXTENSIONS:
            return False, f"Extensão não permitida. Permitidas: {', '.join(self.ALLOWED_EXTENSIONS)}"
        
        if file_path.stat().st_size > self.MAX_BACKUP_SIZE:
            return False, f"Arquivo muito grande. Máximo: {self.MAX_BACKUP_SIZE / (1024*1024):.0f}MB"
        
        return True, "Arquivo válido"
    
    def _log_backup_activity(self, action: str, user: Optional[User], details: str) -> None:
        """Registra atividade de backup para auditoria completa
        
        Args:
            action: Tipo de ação realizada
            user: Usuário que executou a ação
            details: Detalhes da operação
        """
        try:
            # Só registrar se houver usuário
            if user:
                UserActivityLog.objects.create(
                    user=user,
                    action=action,
                    details=details
                )
                logger.debug(f"Atividade registrada: {action} - {details}")
            else:
                logger.debug(f"Atividade do sistema: {action} - {details}")
        except Exception as e:
            # Não falhar operação por erro de log
            logger.warning(f"Erro ao registrar atividade de backup: {e}")
            pass
    
    def get_backup_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas detalhadas dos backups do sistema
        
        Returns:
            Dicionário com estatísticas completas
        """
        try:
            stats = {
                'total_backups': BackupMetadata.objects.count(),
                'by_type': {},
                'by_status': {},
                'total_size': 0,
                'oldest_backup': None,
                'newest_backup': None,
                'failed_backups': 0,
                'average_size': 0
            }
            
            # Estatísticas por tipo
            for backup_type in ['database', 'media', 'configuration']:
                count = BackupMetadata.objects.filter(backup_type=backup_type).count()
                stats['by_type'][backup_type] = count
            
            # Estatísticas por status
            for status in ['completed', 'failed', 'in_progress']:
                count = BackupMetadata.objects.filter(status=status).count()
                stats['by_status'][status] = count
            
            # Tamanho total e datas
            backups = BackupMetadata.objects.all()
            if backups.exists():
                total_size = sum(b.file_size or 0 for b in backups)
                stats['total_size'] = total_size
                stats['average_size'] = total_size / backups.count() if backups.count() > 0 else 0
                stats['oldest_backup'] = backups.order_by('created_at').first().created_at
                stats['newest_backup'] = backups.order_by('-created_at').first().created_at
                stats['failed_backups'] = backups.filter(status='failed').count()
            
            logger.debug(f"Estatísticas de backup geradas: {stats['total_backups']} backups")
            return stats
            
        except Exception as e:
            logger.error(f"Erro ao gerar estatísticas de backup: {e}")
            return {'error': str(e)}
    
    def cleanup_old_backups(self, days_to_keep: int = 30, user: Optional[User] = None) -> Tuple[bool, str, int]:
        """Remove backups antigos baseado em política de retenção
        
        Args:
            days_to_keep: Número de dias para manter os backups
            user: Usuário executando a limpeza
            
        Returns:
            Tuple[bool, str, int]: (sucesso, mensagem, quantidade_removida)
        """
        try:
            logger.info(f"Iniciando limpeza de backups antigos (manter {days_to_keep} dias)")
            
            cutoff_date = timezone.now() - timezone.timedelta(days=days_to_keep)
            old_backups = BackupMetadata.objects.filter(
                created_at__lt=cutoff_date,
                status='completed'  # Só remover backups completos
            )
            
            removed_count = 0
            errors = []
            
            for backup in old_backups:
                try:
                    backup_file = Path(backup.file_path)
                    
                    # Remover arquivo físico
                    if backup_file.exists():
                        backup_file.unlink()
                    
                    # Remover arquivo de metadados
                    metadata_file = backup_file.with_suffix('.metadata.json')
                    if metadata_file.exists():
                        metadata_file.unlink()
                    
                    # Remover registro do banco
                    backup.delete()
                    removed_count += 1
                    
                    logger.debug(f"Backup removido: {backup.slug}")
                    
                except Exception as e:
                    error_msg = f"Erro ao remover backup {backup.slug}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            # Registrar atividade
            self._log_backup_activity(
                'cleanup_old_backups',
                user,
                f'Removidos {removed_count} backups antigos (>{days_to_keep} dias)'
            )
            
            if errors:
                return False, f'Limpeza parcial: {removed_count} removidos, {len(errors)} erros', removed_count
            
            logger.info(f"Limpeza concluída: {removed_count} backups removidos")
            return True, f'Limpeza concluída: {removed_count} backups removidos', removed_count
            
        except Exception as e:
            logger.error(f"Erro na limpeza de backups: {e}")
            return False, f'Erro na limpeza: {str(e)}', 0
    
    def validate_service_configuration(self) -> Dict[str, Any]:
        """Valida a configuração do serviço de backup
        
        Returns:
            Dicionário com status da validação
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'checks': {
                'directories_exist': False,
                'directories_writable': False,
                'database_accessible': False,
                'disk_space_sufficient': False,
                'settings_configured': False
            }
        }
        
        try:
            # Verificar diretórios de backup
            try:
                self._ensure_backup_directories()
                validation_result['checks']['directories_exist'] = True
                
                # Testar escrita nos diretórios
                for directory in [self.database_backup_dir, self.media_backup_dir, self.config_backup_dir]:
                    test_file = directory / 'test_write.tmp'
                    try:
                        test_file.write_text('test')
                        test_file.unlink()
                        validation_result['checks']['directories_writable'] = True
                    except Exception:
                        validation_result['errors'].append(f'Diretório não gravável: {directory}')
                        validation_result['valid'] = False
                        
            except Exception as e:
                validation_result['errors'].append(f'Erro ao verificar diretórios: {e}')
                validation_result['valid'] = False
            
            # Verificar acesso ao banco de dados
            try:
                BackupMetadata.objects.count()
                validation_result['checks']['database_accessible'] = True
            except Exception as e:
                validation_result['errors'].append(f'Banco de dados inacessível: {e}')
                validation_result['valid'] = False
            
            # Verificar espaço em disco
            try:
                if self._check_disk_space(self.database_backup_dir, 100):
                    validation_result['checks']['disk_space_sufficient'] = True
                else:
                    validation_result['warnings'].append('Espaço em disco baixo')
            except Exception as e:
                validation_result['warnings'].append(f'Erro ao verificar espaço: {e}')
            
            # Verificar configurações
            required_settings = ['MEDIA_ROOT', 'DATABASES']
            missing_settings = []
            
            for setting in required_settings:
                if not hasattr(settings, setting):
                    missing_settings.append(setting)
            
            if missing_settings:
                validation_result['errors'].append(f'Configurações ausentes: {", ".join(missing_settings)}')
                validation_result['valid'] = False
            else:
                validation_result['checks']['settings_configured'] = True
            
            logger.info(f"Validação do serviço concluída: {'✓' if validation_result['valid'] else '✗'}")
            return validation_result
            
        except Exception as e:
            logger.error(f"Erro na validação do serviço: {e}")
            return {
                'valid': False,
                'errors': [f'Erro crítico na validação: {str(e)}'],
                'warnings': [],
                'checks': {}
            }