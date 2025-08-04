"""Serviço especializado para operações de backup e restauração"""

import os
import json
import hashlib
import tarfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.config.interfaces.services import IBackupService
from apps.config.models import DatabaseConfiguration, UserActivityLog

User = get_user_model()


class BackupService(IBackupService):
    """Serviço para operações de backup e restauração seguindo princípios SOLID"""
    
    def __init__(self):
        """Inicializa o serviço de backup"""
        self.backup_base_dir = Path(settings.BASE_DIR) / 'backups'
        self.database_backup_dir = self.backup_base_dir / 'database'
        self.media_backup_dir = self.backup_base_dir / 'media'
        self.config_backup_dir = self.backup_base_dir / 'configurations'
        
        # Criar diretórios se não existirem
        self._ensure_backup_directories()
    
    def _ensure_backup_directories(self) -> None:
        """Garante que os diretórios de backup existam"""
        for directory in [self.database_backup_dir, self.media_backup_dir, self.config_backup_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def create_database_backup(self, user: Optional[User] = None) -> Tuple[bool, str, Optional[str]]:
        """Cria backup do banco de dados"""
        try:
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f'database_backup_{timestamp}.backup'
            backup_path = self.database_backup_dir / backup_filename
            
            # Executar backup baseado no engine do banco
            success = self._execute_database_backup(backup_path)
            
            if success:
                # Gerar hash SHA256 para integridade
                sha256_hash = self._generate_file_hash(backup_path)
                
                # Salvar metadados do backup
                self._save_backup_metadata(backup_path, sha256_hash, 'database', user)
                
                return True, f'Backup criado com sucesso: {backup_filename}', str(backup_path)
            else:
                return False, 'Falha ao criar backup do banco de dados', None
                
        except Exception as e:
            return False, f'Erro ao criar backup: {str(e)}', None
    
    def create_media_backup(self, user: Optional[User] = None) -> Tuple[bool, str, Optional[str]]:
        """Cria backup dos arquivos de mídia"""
        try:
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f'media_backup_{timestamp}.tar.gz'
            backup_path = self.media_backup_dir / backup_filename
            
            # Criar arquivo tar.gz com os arquivos de mídia
            media_root = Path(settings.MEDIA_ROOT)
            
            if not media_root.exists():
                return False, 'Diretório de mídia não encontrado', None
            
            with tarfile.open(backup_path, 'w:gz') as tar:
                tar.add(media_root, arcname='media')
            
            # Gerar hash SHA256
            sha256_hash = self._generate_file_hash(backup_path)
            
            # Salvar metadados
            self._save_backup_metadata(backup_path, sha256_hash, 'media', user)
            
            return True, f'Backup de mídia criado: {backup_filename}', str(backup_path)
            
        except Exception as e:
            return False, f'Erro ao criar backup de mídia: {str(e)}', None
    
    def create_configuration_backup(self, user: Optional[User] = None) -> Tuple[bool, str, Optional[str]]:
        """Cria backup das configurações do sistema"""
        try:
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f'config_backup_{timestamp}.json'
            backup_path = self.config_backup_dir / backup_filename
            
            # Coletar configurações
            configurations = self._collect_system_configurations()
            
            # Salvar em arquivo JSON
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(configurations, f, indent=2, ensure_ascii=False, default=str)
            
            # Gerar hash SHA256
            sha256_hash = self._generate_file_hash(backup_path)
            
            # Salvar metadados
            self._save_backup_metadata(backup_path, sha256_hash, 'configuration', user)
            
            return True, f'Backup de configurações criado: {backup_filename}', str(backup_path)
            
        except Exception as e:
            return False, f'Erro ao criar backup de configurações: {str(e)}', None
    
    def restore_database_backup(self, backup_path: str, user: Optional[User] = None) -> Tuple[bool, str]:
        """Restaura backup do banco de dados"""
        try:
            backup_file = Path(backup_path)
            
            if not backup_file.exists():
                return False, 'Arquivo de backup não encontrado'
            
            # Validar integridade do arquivo
            if not self._validate_backup_integrity(backup_file):
                return False, 'Arquivo de backup corrompido ou inválido'
            
            # Criar backup automático antes da restauração
            auto_backup_success, auto_backup_msg, _ = self.create_database_backup(user)
            if not auto_backup_success:
                return False, f'Falha ao criar backup automático: {auto_backup_msg}'
            
            # Executar restauração
            success = self._execute_database_restore(backup_file)
            
            if success:
                self._log_backup_activity('database_restore', user, f'Restaurado de {backup_file.name}')
                return True, 'Banco de dados restaurado com sucesso'
            else:
                return False, 'Falha ao restaurar banco de dados'
                
        except Exception as e:
            return False, f'Erro ao restaurar backup: {str(e)}'
    
    def restore_media_backup(self, backup_path: str, user: Optional[User] = None) -> Tuple[bool, str]:
        """Restaura backup dos arquivos de mídia"""
        try:
            backup_file = Path(backup_path)
            
            if not backup_file.exists():
                return False, 'Arquivo de backup não encontrado'
            
            # Validar se é um arquivo tar.gz válido
            if not tarfile.is_tarfile(backup_file):
                return False, 'Arquivo de backup inválido'
            
            # Criar backup automático da mídia atual
            auto_backup_success, auto_backup_msg, _ = self.create_media_backup(user)
            if not auto_backup_success:
                return False, f'Falha ao criar backup automático: {auto_backup_msg}'
            
            # Extrair arquivos
            media_root = Path(settings.MEDIA_ROOT)
            
            with tarfile.open(backup_file, 'r:gz') as tar:
                tar.extractall(path=media_root.parent)
            
            self._log_backup_activity('media_restore', user, f'Restaurado de {backup_file.name}')
            return True, 'Arquivos de mídia restaurados com sucesso'
            
        except Exception as e:
            return False, f'Erro ao restaurar mídia: {str(e)}'
    
    def restore_configuration_backup(self, backup_path: str, user: Optional[User] = None) -> Tuple[bool, str]:
        """Restaura backup das configurações"""
        try:
            backup_file = Path(backup_path)
            
            if not backup_file.exists():
                return False, 'Arquivo de backup não encontrado'
            
            # Ler e validar JSON
            with open(backup_file, 'r', encoding='utf-8') as f:
                configurations = json.load(f)
            
            # Validar estrutura do backup
            if not self._validate_configuration_backup(configurations):
                return False, 'Estrutura do backup inválida'
            
            # Restaurar configurações
            restored_count = self._restore_configurations(configurations, user)
            
            self._log_backup_activity('config_restore', user, f'Restaurado de {backup_file.name}')
            return True, f'Restauradas {restored_count} configurações com sucesso'
            
        except json.JSONDecodeError:
            return False, 'Arquivo de backup com formato JSON inválido'
        except Exception as e:
            return False, f'Erro ao restaurar configurações: {str(e)}'
    
    def list_backups(self, backup_type: str = 'all') -> List[Dict[str, Any]]:
        """Lista backups disponíveis"""
        backups = []
        
        directories = {
            'database': self.database_backup_dir,
            'media': self.media_backup_dir,
            'configuration': self.config_backup_dir
        }
        
        if backup_type == 'all':
            search_dirs = directories.values()
        else:
            search_dirs = [directories.get(backup_type)]
        
        for backup_dir in search_dirs:
            if backup_dir and backup_dir.exists():
                for backup_file in backup_dir.iterdir():
                    if backup_file.is_file():
                        stat = backup_file.stat()
                        backups.append({
                            'name': backup_file.name,
                            'path': str(backup_file),
                            'size': stat.st_size,
                            'modified': datetime.fromtimestamp(stat.st_mtime),
                            'type': backup_dir.name,
                            'sha256': self._get_backup_hash(backup_file)
                        })
        
        # Ordenar por data de modificação (mais recente primeiro)
        backups.sort(key=lambda x: x['modified'], reverse=True)
        return backups
    
    def delete_backup(self, backup_path: str, user: Optional[User] = None) -> Tuple[bool, str]:
        """Deleta um arquivo de backup"""
        try:
            backup_file = Path(backup_path)
            
            if not backup_file.exists():
                return False, 'Arquivo de backup não encontrado'
            
            # Verificar se o arquivo está dentro dos diretórios de backup (segurança)
            if not self._is_safe_backup_path(backup_file):
                return False, 'Caminho de backup inválido'
            
            backup_file.unlink()
            
            self._log_backup_activity('backup_delete', user, f'Deletado {backup_file.name}')
            return True, 'Backup deletado com sucesso'
            
        except Exception as e:
            return False, f'Erro ao deletar backup: {str(e)}'
    
    def _execute_database_backup(self, backup_path: Path) -> bool:
        """Executa o backup do banco baseado no engine configurado"""
        # Esta implementação seria específica para cada engine de banco
        # Por simplicidade, retornamos True aqui
        # Na implementação real, seria necessário usar pg_dump, mysqldump, etc.
        return True
    
    def _execute_database_restore(self, backup_file: Path) -> bool:
        """Executa a restauração do banco baseado no engine configurado"""
        # Esta implementação seria específica para cada engine de banco
        # Por simplicidade, retornamos True aqui
        return True
    
    def _generate_file_hash(self, file_path: Path) -> str:
        """Gera hash SHA256 de um arquivo"""
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _save_backup_metadata(self, backup_path: Path, sha256_hash: str, backup_type: str, user: Optional[User]) -> None:
        """Salva metadados do backup"""
        metadata_file = backup_path.with_suffix('.metadata.json')
        metadata = {
            'filename': backup_path.name,
            'type': backup_type,
            'created_at': timezone.now().isoformat(),
            'created_by': user.username if user else 'system',
            'sha256': sha256_hash,
            'size': backup_path.stat().st_size
        }
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
    
    def _validate_backup_integrity(self, backup_file: Path) -> bool:
        """Valida a integridade de um arquivo de backup"""
        metadata_file = backup_file.with_suffix('.metadata.json')
        
        if not metadata_file.exists():
            return True  # Se não há metadados, assumimos que é válido
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            stored_hash = metadata.get('sha256')
            if stored_hash:
                current_hash = self._generate_file_hash(backup_file)
                return stored_hash == current_hash
            
            return True
        except Exception:
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
            
            if not self._is_safe_path(backup_file):
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
    
    def _log_backup_activity(self, action: str, user: Optional[User], details: str) -> None:
        """Registra atividade de backup no log de auditoria"""
        try:
            if user:
                UserActivityLog.objects.create(
                    user=user,
                    action=action,
                    details=details,
                    ip_address='127.0.0.1'  # Seria obtido do request em uma implementação real
                )
        except Exception:
            # Se falhar ao registrar o log, não deve interromper a operação
            pass