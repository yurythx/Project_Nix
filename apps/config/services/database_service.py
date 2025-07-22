"""
Serviço para gerenciar configurações de banco de dados
"""
import os
import json
from pathlib import Path
from django.conf import settings
from django.db import connections
from django.core.management import call_command
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.config.models import DatabaseConfiguration, UserActivityLog
from apps.config.interfaces.services import IDatabaseService

User = get_user_model()


class DatabaseService(IDatabaseService):
    """Serviço para gerenciar configurações de banco de dados"""
    
    def get_active_configuration(self):
        """Retorna a configuração ativa"""
        return DatabaseConfiguration.objects.filter(
            is_active=True
        ).first()
    
    def get_default_configuration(self):
        """Retorna a configuração padrão"""
        return DatabaseConfiguration.objects.filter(
            is_default=True
        ).first()
    
    def list_configurations(self):
        """Lista todas as configurações"""
        return DatabaseConfiguration.objects.all().order_by(
            '-is_default', '-is_active', 'name'
        )
    
    def create_configuration(self, name, engine, database_name, **kwargs):
        """Cria uma nova configuração de banco"""
        config = DatabaseConfiguration(
            name=name,
            engine=engine,
            name_db=database_name,
            **kwargs
        )
        config.save()
        return config
    
    def test_configuration(self, config_id):
        """Testa uma configuração específica"""
        try:
            config = DatabaseConfiguration.objects.get(id=config_id)
            success, message = config.test_connection()
            config.save()
            return success, message, config
        except DatabaseConfiguration.DoesNotExist:
            return False, "Configuração não encontrada", None
    
    def activate_configuration(self, config_id, user=None):
        """Ativa uma configuração específica"""
        try:
            config = DatabaseConfiguration.objects.get(id=config_id)
            
            # Testar conexão antes de ativar
            success, test_message = config.test_connection()
            if not success:
                return False, f"Erro na conexão: {test_message}", config
            
            # Ativar configuração
            success, message = config.activate_configuration()
            
            if success and user:
                # Registrar ativação no log
                UserActivityLog.objects.create(
                    user=user,
                    action='database_config_activated',
                    description=f'Configuração de banco "{config.name}" ativada',
                    metadata={
                        'config_id': config.id,
                        'config_name': config.name,
                        'engine': config.engine,
                    }
                )
            
            return success, message, config
            
        except DatabaseConfiguration.DoesNotExist:
            return False, "Configuração não encontrada", None
    
    def switch_database(self, config_id, user=None):
        """Troca o banco de dados ativo"""
        success, message, config = self.activate_configuration(config_id, user)
        
        if success:
            # Fechar conexões existentes
            connections.close_all()
            
            # Recarregar configurações do Django
            self._reload_django_settings()
            
            return True, f"Banco de dados trocado para '{config.name}' com sucesso", config
        
        return success, message, config
    
    def _reload_django_settings(self):
        """Recarrega as configurações do Django"""
        # Nota: Em produção, seria necessário reiniciar o servidor
        # Esta função é mais útil para desenvolvimento
        try:
            # Limpar cache de configurações
            if hasattr(settings, '_wrapped'):
                delattr(settings, '_wrapped')
            
            # Recarregar variáveis de ambiente
            from django.core.management.utils import get_random_secret_key
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
            
            return True
        except Exception as e:
            return False
    
    def backup_configurations(self):
        """Cria backup de todas as configurações"""
        try:
            # Criar diretório de backup
            backup_dir = Path('backups/database_configs')
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Nome do arquivo
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            backup_file = backup_dir / f'all_db_configs_{timestamp}.json'
            
            # Coletar dados
            configs = DatabaseConfiguration.objects.all()
            backup_data = {
                'timestamp': timezone.now().isoformat(),
                'total_configs': configs.count(),
                'configurations': []
            }
            
            for config in configs:
                config_data = {
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
                    'created_at': config.created_at.isoformat() if config.created_at else None,
                }
                backup_data['configurations'].append(config_data)
            
            # Salvar backup
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            return True, f"Backup salvo em {backup_file}", backup_file
            
        except Exception as e:
            return False, f"Erro ao criar backup: {str(e)}", None
    
    def restore_configurations(self, backup_file_path, user=None):
        """Restaura configurações de um backup"""
        try:
            backup_path = Path(backup_file_path)
            if not backup_path.exists():
                return False, "Arquivo de backup não encontrado", None
            
            # Ler backup
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            restored_count = 0
            errors = []
            
            for config_data in backup_data.get('configurations', []):
                try:
                    # Verificar se já existe
                    existing = DatabaseConfiguration.objects.filter(
                        name=config_data['name']
                    ).first()
                    
                    if existing:
                        # Atualizar existente
                        for key, value in config_data.items():
                            if key not in ['created_at']:
                                setattr(existing, key, value)
                        
                        if user:
                            existing.updated_by = user
                        
                        existing.save()
                    else:
                        # Criar novo
                        config = DatabaseConfiguration(
                            created_by=user,
                            updated_by=user,
                            **config_data
                        )
                        config.save()
                    
                    restored_count += 1
                    
                except Exception as e:
                    errors.append(f"Erro ao restaurar {config_data.get('name', 'desconhecido')}: {str(e)}")
            
            return True, f"Restauradas {restored_count} configurações", {
                'restored': restored_count,
                'errors': errors
            }
            
        except Exception as e:
            return False, f"Erro ao restaurar backup: {str(e)}", None
    
    def get_connection_info(self):
        """Retorna informações da conexão atual"""
        try:
            # Obter configuração ativa
            active_config = self.get_active_configuration()
            
            if not active_config:
                return {
                    'active_config': None,
                    'connection_status': 'no_config',
                    'message': 'Nenhuma configuração ativa encontrada'
                }
            
            # Testar conexão
            success, message = active_config.test_connection()
            
            return {
                'active_config': {
                    'name': active_config.name,
                    'engine': active_config.engine,
                    'database': active_config.name_db,
                    'host': active_config.host,
                    'port': active_config.port,
                    'user': active_config.user,
                },
                'connection_status': 'connected' if success else 'error',
                'message': message,
                'tested_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            return {
                'active_config': None,
                'connection_status': 'error',
                'message': f'Erro ao obter informações: {str(e)}'
            }
    
    def migrate_database(self, config_id=None):
        """Executa migrações no banco de dados"""
        try:
            if config_id:
                # Migrar para configuração específica
                success, message, config = self.activate_configuration(config_id)
                if not success:
                    return False, f"Erro ao ativar configuração: {message}"
            
            # Executar migrações
            call_command('migrate', verbosity=0)
            
            return True, "Migrações executadas com sucesso"
            
        except Exception as e:
            return False, f"Erro ao executar migrações: {str(e)}"
