from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
import json

User = get_user_model()


class EmailConfiguration(models.Model):
    """Modelo para múltiplas configurações de email"""
    
    name = models.CharField(
        max_length=100,
        verbose_name='Nome da Configuração',
        help_text='Nome identificador para esta configuração (ex: Gmail Principal, Outlook Backup)'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='Descrição',
        help_text='Descrição detalhada desta configuração'
    )
    
    # Configurações SMTP
    email_backend = models.CharField(
        max_length=200,
        default='django.core.mail.backends.smtp.EmailBackend',
        verbose_name='Backend de Email'
    )
    
    email_host = models.CharField(
        max_length=200,
        verbose_name='Servidor SMTP',
        help_text='Ex: smtp.gmail.com'
    )
    
    email_port = models.IntegerField(
        default=587,
        verbose_name='Porta SMTP',
        help_text='Geralmente 587 (TLS) ou 465 (SSL)'
    )
    
    email_host_user = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Usuário SMTP',
        help_text='Email ou username para autenticação'
    )

    email_host_password = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Senha SMTP',
        help_text='Senha ou senha de app'
    )
    
    email_use_tls = models.BooleanField(
        default=True,
        verbose_name='Usar TLS',
        help_text='Recomendado para a maioria dos servidores'
    )
    
    email_use_ssl = models.BooleanField(
        default=False,
        verbose_name='Usar SSL',
        help_text='Alternativa ao TLS'
    )
    
    default_from_email = models.EmailField(
        verbose_name='Email Remetente',
        help_text='Email que aparecerá como remetente'
    )
    
    email_timeout = models.IntegerField(
        default=30,
        verbose_name='Timeout (segundos)',
        help_text='Tempo limite para conexão'
    )
    
    # Configurações de controle
    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativo',
        help_text='Se esta configuração está disponível para uso'
    )
    
    is_default = models.BooleanField(
        default=False,
        verbose_name='Padrão',
        help_text='Se esta é a configuração padrão do sistema'
    )
    
    # Metadados
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_configs_created'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_configs_updated'
    )
    
    # Estatísticas de uso
    last_tested_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Último Teste'
    )
    
    last_test_result = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Resultado do Último Teste'
    )
    
    emails_sent_count = models.IntegerField(
        default=0,
        verbose_name='Emails Enviados',
        help_text='Contador de emails enviados com esta configuração'
    )
    
    class Meta:
        verbose_name = 'Configuração de Email'
        verbose_name_plural = 'Configurações de Email'
        ordering = ['-is_default', '-is_active', 'name']
    
    def __str__(self):
        status = "🟢" if self.is_active else "🔴"
        default = " (Padrão)" if self.is_default else ""
        return f"{status} {self.name}{default}"
    
    def clean(self):
        """Validações customizadas"""
        # Validar que apenas uma configuração pode ser padrão
        if self.is_default:
            existing_default = EmailConfiguration.objects.filter(
                is_default=True
            ).exclude(pk=self.pk)
            
            if existing_default.exists():
                raise ValidationError(
                    'Já existe uma configuração padrão. '
                    'Desative a atual antes de definir uma nova.'
                )
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def get_config_dict(self):
        """Retorna configuração como dicionário para uso no EmailService"""
        return {
            'EMAIL_BACKEND': self.email_backend,
            'EMAIL_HOST': self.email_host,
            'EMAIL_PORT': self.email_port,
            'EMAIL_HOST_USER': self.email_host_user,
            'EMAIL_HOST_PASSWORD': self.email_host_password,
            'EMAIL_USE_TLS': self.email_use_tls,
            'EMAIL_USE_SSL': self.email_use_ssl,
            'DEFAULT_FROM_EMAIL': self.default_from_email,
            'EMAIL_TIMEOUT': self.email_timeout,
        }
    
    def test_connection(self):
        """Testa a conexão com esta configuração"""
        from apps.accounts.services.email_service import EmailService
        
        # Criar EmailService temporário com esta configuração
        email_service = EmailService()
        email_service.config = self.get_config_dict()
        
        try:
            success, message = email_service.test_connection()
            
            # Salvar resultado do teste
            self.last_tested_at = timezone.now()
            self.last_test_result = {
                'success': success,
                'message': message,
                'tested_at': self.last_tested_at.isoformat()
            }
            self.save(update_fields=['last_tested_at', 'last_test_result'])

            return success, message

        except Exception as e:
            error_message = f'Erro no teste: {str(e)}'
            self.last_tested_at = timezone.now()
            self.last_test_result = {
                'success': False,
                'message': error_message,
                'tested_at': self.last_tested_at.isoformat()
            }
            self.save(update_fields=['last_tested_at', 'last_test_result'])
            
            return False, error_message
    
    def send_test_email(self, recipient_email, user_name=None):
        """Envia email de teste usando esta configuração"""
        from apps.accounts.services.email_service import EmailService
        
        email_service = EmailService()
        email_service.config = self.get_config_dict()
        
        try:
            success, message = email_service.send_test_email(recipient_email, user_name)
            
            if success:
                self.emails_sent_count += 1
                self.save(update_fields=['emails_sent_count'])
            
            return success, message
            
        except Exception as e:
            return False, f'Erro ao enviar email: {str(e)}'
    
    @classmethod
    def get_default(cls):
        """Retorna a configuração padrão"""
        try:
            return cls.objects.filter(is_default=True, is_active=True).first()
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def get_active_configs(cls):
        """Retorna todas as configurações ativas"""
        return cls.objects.filter(is_active=True)


class DatabaseConfiguration(models.Model):
    """Modelo para múltiplas configurações de banco de dados"""
    
    name = models.CharField(
        max_length=100,
        verbose_name='Nome da Configuração',
        help_text='Nome identificador (ex: PostgreSQL Principal, MySQL Backup)'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='Descrição'
    )
    
    # Configurações do banco
    engine = models.CharField(
        max_length=200,
        verbose_name='Engine do Banco',
        choices=[
            ('django.db.backends.postgresql', 'PostgreSQL'),
            ('django.db.backends.mysql', 'MySQL'),
            ('django.db.backends.sqlite3', 'SQLite'),
            ('django.db.backends.oracle', 'Oracle'),
        ],
        default='django.db.backends.postgresql'
    )
    
    name_db = models.CharField(
        max_length=200,
        verbose_name='Nome do Banco',
        help_text='Nome da base de dados'
    )
    
    user = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Usuário',
        help_text='Usuário para conexão (não necessário para SQLite)'
    )
    
    password = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Senha',
        help_text='Senha do usuário'
    )
    
    host = models.CharField(
        max_length=200,
        blank=True,
        default='localhost',
        verbose_name='Host',
        help_text='Endereço do servidor'
    )
    
    port = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='Porta',
        help_text='Porta de conexão (deixe vazio para padrão)'
    )
    
    # Opções adicionais
    options = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Opções Adicionais',
        help_text='Configurações extras em formato JSON'
    )
    
    # Configurações de controle
    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )
    
    is_default = models.BooleanField(
        default=False,
        verbose_name='Padrão'
    )
    
    # Metadados
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='db_configs_created'
    )
    
    # Estatísticas
    last_tested_at = models.DateTimeField(null=True, blank=True)
    last_test_result = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = 'Configuração de Banco de Dados'
        verbose_name_plural = 'Configurações de Banco de Dados'
        ordering = ['-is_default', '-is_active', 'name']
    
    def __str__(self):
        status = "🟢" if self.is_active else "🔴"
        default = " (Padrão)" if self.is_default else ""
        return f"{status} {self.name}{default}"
    
    def clean(self):
        """Validações customizadas"""
        if self.is_default:
            existing_default = DatabaseConfiguration.objects.filter(
                is_default=True
            ).exclude(pk=self.pk)
            
            if existing_default.exists():
                raise ValidationError(
                    'Já existe uma configuração padrão de banco de dados.'
                )
    
    def get_config_dict(self):
        """Retorna configuração como dicionário Django"""
        config = {
            'ENGINE': self.engine,
            'NAME': self.name_db,
        }
        
        if self.user:
            config['USER'] = self.user
        if self.password:
            config['PASSWORD'] = self.password
        if self.host:
            config['HOST'] = self.host
        if self.port:
            config['PORT'] = self.port
        if self.options:
            config['OPTIONS'] = self.options
        
        return config
    
    def test_connection(self):
        """Testa a conexão com este banco"""
        from django.utils import timezone
        import os

        try:
            # Para SQLite, verificar se é um arquivo válido
            if self.engine == 'django.db.backends.sqlite3':
                if not self.name_db:
                    return False, 'Nome do banco SQLite é obrigatório'

                # Se for :memory:, é válido
                if self.name_db == ':memory:':
                    success_message = 'Configuração SQLite em memória válida'
                else:
                    # Verificar se o diretório existe
                    db_path = self.name_db
                    if not os.path.isabs(db_path):
                        # Caminho relativo, usar diretório do projeto
                        db_path = os.path.join(os.getcwd(), db_path)

                    db_dir = os.path.dirname(db_path)
                    if db_dir and not os.path.exists(db_dir):
                        return False, f'Diretório não existe: {db_dir}'

                    success_message = f'Configuração SQLite válida: {self.name_db}'

            else:
                # Para outros bancos, verificar configurações básicas
                if not self.host:
                    return False, 'Host é obrigatório para este tipo de banco'

                if not self.name_db:
                    return False, 'Nome do banco é obrigatório'

                if not self.user:
                    return False, 'Usuário é obrigatório para este tipo de banco'

                # Tentar importar o driver específico
                if self.engine == 'django.db.backends.postgresql':
                    try:
                        import psycopg2
                        success_message = 'Configuração PostgreSQL válida (driver disponível)'
                    except ImportError:
                        return False, 'Driver PostgreSQL (psycopg2) não está instalado'

                elif self.engine == 'django.db.backends.mysql':
                    try:
                        import MySQLdb
                        success_message = 'Configuração MySQL válida (driver MySQLdb disponível)'
                    except ImportError:
                        try:
                            import pymysql
                            success_message = 'Configuração MySQL válida (driver PyMySQL disponível)'
                        except ImportError:
                            return False, 'Driver MySQL (MySQLdb ou PyMySQL) não está instalado'

                else:
                    success_message = f'Configuração {self.get_engine_display()} válida'

            # Salvar resultado de sucesso
            self.last_tested_at = timezone.now()
            self.last_test_result = {
                'success': True,
                'message': success_message,
                'tested_at': self.last_tested_at.isoformat()
            }
            self.save(update_fields=['last_tested_at', 'last_test_result'])

            return True, success_message

        except Exception as e:
            error_message = f'Erro na validação: {str(e)}'

            # Salvar erro
            self.last_tested_at = timezone.now()
            self.last_test_result = {
                'success': False,
                'message': error_message,
                'tested_at': self.last_tested_at.isoformat()
            }
            self.save(update_fields=['last_tested_at', 'last_test_result'])

            return False, error_message
    
    @classmethod
    def get_default(cls):
        """Retorna a configuração padrão"""
        return cls.objects.filter(is_default=True, is_active=True).first()
    
    @classmethod
    def get_active_configs(cls):
        """Retorna todas as configurações ativas"""
        return cls.objects.filter(is_active=True)

    def update_env_file(self):
        """Atualiza o arquivo .env com esta configuração"""
        import os
        from pathlib import Path
        from django.conf import settings

        # Determinar qual arquivo .env usar
        env_files = ['.env', '.env.local', '.env.prod']
        env_path = None

        # Procurar arquivo .env existente
        for env_file in env_files:
            path = Path(env_file)
            if path.exists():
                env_path = path
                break

        # Se não encontrar, criar .env
        if not env_path:
            env_path = Path('.env')

        # Ler arquivo atual ou criar novo
        env_lines = []
        if env_path.exists():
            with open(env_path, 'r', encoding='utf-8') as f:
                env_lines = f.readlines()

        # Variáveis de banco de dados
        db_vars = {
            'DB_ENGINE': self.engine,
            'DB_NAME': self.name_db,
            'DB_USER': self.user or '',
            'DB_PASSWORD': self.password or '',
            'DB_HOST': self.host or '',
            'DB_PORT': self.port or '',
        }

        # Adicionar DATABASE_URL se for PostgreSQL ou MySQL
        if self.engine in ['django.db.backends.postgresql', 'django.db.backends.mysql']:
            if self.engine == 'django.db.backends.postgresql':
                protocol = 'postgresql'
            else:
                protocol = 'mysql'

            if self.user and self.password and self.host:
                database_url = f"{protocol}://{self.user}:{self.password}@{self.host}:{self.port or '5432'}/{self.name_db}"
                db_vars['DATABASE_URL'] = database_url

        # Atualizar ou adicionar variáveis
        updated_lines = []
        updated_vars = set()
        db_section_added = False

        for line in env_lines:
            original_line = line
            line_stripped = line.strip()

            # Pular linhas de comentário sobre configurações de banco duplicadas
            if line_stripped.startswith('# Configurações de Banco de Dados atualizadas automaticamente'):
                continue

            if '=' in line_stripped and not line_stripped.startswith('#'):
                var_name = line_stripped.split('=')[0].strip()
                if var_name in db_vars:
                    # Só adicionar se ainda não foi adicionado
                    if var_name not in updated_vars:
                        updated_lines.append(f"{var_name}={db_vars[var_name]}\n")
                        updated_vars.add(var_name)
                    # Pular a linha original para evitar duplicação
                    continue
                else:
                    updated_lines.append(original_line)
            else:
                updated_lines.append(original_line)

        # Adicionar variáveis que não existiam no arquivo
        new_vars = set(db_vars.keys()) - updated_vars
        if new_vars:
            if not db_section_added:
                updated_lines.append("\n# Configurações de Banco de Dados atualizadas automaticamente\n")
                db_section_added = True

            for var_name in new_vars:
                updated_lines.append(f"{var_name}={db_vars[var_name]}\n")

        # Escrever arquivo atualizado
        try:
            with open(env_path, 'w', encoding='utf-8') as f:
                f.writelines(updated_lines)
            return True, f"Arquivo {env_path} atualizado com sucesso"
        except Exception as e:
            return False, f"Erro ao atualizar arquivo {env_path}: {str(e)}"

    def activate_configuration(self):
        """Ativa esta configuração como padrão e atualiza o sistema"""
        from django.utils import timezone

        # Desativar outras configurações padrão
        DatabaseConfiguration.objects.filter(is_default=True).update(is_default=False)

        # Ativar esta configuração
        self.is_default = True
        self.is_active = True
        self.save()

        # Atualizar arquivo .env
        success, message = self.update_env_file()

        if success:
            # Registrar ativação
            from .user_activity_log import UserActivityLog
            UserActivityLog.objects.create(
                action='database_config_activated',
                description=f'Configuração de banco "{self.name}" ativada como padrão',
                metadata={
                    'config_id': self.id,
                    'config_name': self.name,
                    'engine': self.engine,
                    'activated_at': timezone.now().isoformat()
                }
            )

        return success, message

    def get_connection_string(self):
        """Retorna string de conexão para o banco"""
        if self.engine == 'django.db.backends.sqlite3':
            return f"sqlite:///{self.name_db}"

        elif self.engine == 'django.db.backends.postgresql':
            port = self.port or '5432'
            return f"postgresql://{self.user}:{self.password}@{self.host}:{port}/{self.name_db}"

        elif self.engine == 'django.db.backends.mysql':
            port = self.port or '3306'
            return f"mysql://{self.user}:{self.password}@{self.host}:{port}/{self.name_db}"

        elif self.engine == 'django.db.backends.oracle':
            port = self.port or '1521'
            return f"oracle://{self.user}:{self.password}@{self.host}:{port}/{self.name_db}"

        return "Tipo de banco não suportado"

    def get_default_port(self):
        """Retorna a porta padrão para o tipo de banco"""
        defaults = {
            'django.db.backends.postgresql': '5432',
            'django.db.backends.mysql': '3306',
            'django.db.backends.oracle': '1521',
            'django.db.backends.sqlite3': '',
        }
        return defaults.get(self.engine, '')

    def backup_current_config(self):
        """Cria backup da configuração atual antes de ativar nova"""
        from django.conf import settings
        import json
        from pathlib import Path
        from django.utils import timezone

        # Criar diretório de backup se não existir
        backup_dir = Path('backups/database_configs')
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Nome do arquivo de backup
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        backup_file = backup_dir / f'db_config_backup_{timestamp}.json'

        # Dados do backup
        backup_data = {
            'timestamp': timezone.now().isoformat(),
            'previous_config': {
                'name': self.name,
                'engine': self.engine,
                'name_db': self.name_db,
                'user': self.user,
                'host': self.host,
                'port': self.port,
                'options': self.options,
            },
            'django_settings': {
                'DEBUG': getattr(settings, 'DEBUG', None),
                'DATABASES': getattr(settings, 'DATABASES', {}),
            }
        }

        try:
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)

            return True, f"Backup salvo em {backup_file}"
        except Exception as e:
            return False, f"Erro ao criar backup: {str(e)}"
