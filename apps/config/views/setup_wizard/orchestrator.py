from .base import WizardStepHandler, WizardStepError
from django.core.cache import cache
from django.conf import settings
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class SetupWizardOrchestrator:
    def __init__(self, steps: dict):
        self.steps = steps  # dict: nome -> WizardStepHandler

    def process_step(self, step_name, request):
        handler = self.steps.get(step_name)
        if not handler:
            raise WizardStepError(f"Step '{step_name}' não encontrado.")
        return handler.process(request, self)
    
    def test_database_connection(self, config):
        """Testa conexão com banco de dados"""
        try:
            if config['type'] == 'sqlite':
                return self.test_sqlite_connection(config)
            elif config['type'] == 'postgresql':
                return self.test_postgresql_connection(config)
            elif config['type'] == 'mysql':
                return self.test_mysql_connection(config)
            else:
                return False
        except Exception as e:
            logger.error(f"Erro no teste de conexão: {e}")
            return False
    
    def test_sqlite_connection(self, config):
        """Testa conexão SQLite"""
        try:
            import sqlite3
            db_path = config.get('NAME', 'db.sqlite3')
            conn = sqlite3.connect(db_path)
            conn.close()
            return True
        except Exception:
            return False
    
    def test_postgresql_connection(self, config):
        """Testa conexão PostgreSQL"""
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=config.get('HOST', 'localhost'),
                port=config.get('PORT', 5432),
                user=config.get('USER', 'postgres'),
                password=config.get('PASSWORD', ''),
                database=config.get('NAME', 'postgres'),
                connect_timeout=5
            )
            conn.close()
            return True
        except Exception:
            return False
    
    def test_mysql_connection(self, config):
        """Testa conexão MySQL"""
        try:
            import mysql.connector
            conn = mysql.connector.connect(
                host=config.get('HOST', 'localhost'),
                port=config.get('PORT', 3306),
                user=config.get('USER', 'root'),
                password=config.get('PASSWORD', ''),
                database=config.get('NAME', ''),
                connect_timeout=5
            )
            conn.close()
            return True
        except Exception:
            return False
    
    def save_progress(self, step: str, data: dict):
        """Salva progresso no cache"""
        progress = cache.get('setup_wizard_progress', {})
        progress[step] = data
        cache.set('setup_wizard_progress', progress, timeout=3600)  # 1 hora
    
    def apply_all_configurations(self, database_config=None, admin_config=None, email_config=None, security_config=None):
        """Aplica todas as configurações salvas"""
        try:
            progress = cache.get('setup_wizard_progress', {})
            
            # Use provided configs or fall back to cached progress
            database_data = database_config or progress.get('database', {})
            admin_data = admin_config or progress.get('admin', {})
            email_data = email_config or progress.get('email', {})
            security_data = security_config or progress.get('security', {})
            
            # Aplicar configuração do banco
            if database_data:
                self.apply_database_config(database_data)
            
            # Executar migrações do banco de dados
            self.run_migrations()
            
            # Aplicar configuração do admin (após as migrações)
            if admin_data:
                self.apply_admin_config(admin_data)
            
            # Aplicar configuração de email
            if email_data:
                self.apply_email_config(email_data)
            
            # Aplicar configuração de segurança
            if security_data:
                self.apply_security_config(security_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao aplicar configurações: {e}", exc_info=True)
            return False
    
    def run_migrations(self):
        """Executa makemigrations e migrate"""
        try:
            from django.core.management import call_command
            from django.db import connection
            
            logger.info("Executando makemigrations...")
            call_command('makemigrations', verbosity=0)
            
            logger.info("Executando migrate...")
            call_command('migrate', verbosity=0)
            
            logger.info("Migrações concluídas com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao executar migrações: {e}", exc_info=True)
            return False
    
    def apply_database_config(self, config):
        """Aplica configuração do banco de dados ao .env"""
        try:
            env_file = Path(settings.BASE_DIR) / '.env'
            
            # Ler arquivo .env atual
            env_content = ""
            if env_file.exists():
                with open(env_file, 'r', encoding='utf-8') as f:
                    env_content = f.read()
            
            # Handle both frontend format (lowercase) and backend format
            db_type = config.get('type', config.get('TYPE', 'sqlite'))
            
            if db_type == 'sqlite':
                db_name = config.get('name', config.get('NAME', 'db.sqlite3'))
                env_content = self.update_env_var(env_content, 'DATABASE_URL', f'sqlite:///{db_name}')
                env_content = self.update_env_var(env_content, 'DB_ENGINE', 'django.db.backends.sqlite3')
                env_content = self.update_env_var(env_content, 'DB_NAME', db_name)
                env_content = self.update_env_var(env_content, 'DB_USER', '')
                env_content = self.update_env_var(env_content, 'DB_PASSWORD', '')
                env_content = self.update_env_var(env_content, 'DB_HOST', '')
                env_content = self.update_env_var(env_content, 'DB_PORT', '')
                
            elif db_type == 'postgresql':
                db_name = config.get('name', config.get('NAME', 'fireflies'))
                host = config.get('host', config.get('HOST', 'localhost'))
                port = config.get('port', config.get('PORT', '5432'))
                user = config.get('user', config.get('USER', 'postgres'))
                password = config.get('password', config.get('PASSWORD', ''))
                
                env_content = self.update_env_var(env_content, 'DATABASE_URL', f'postgresql://{user}:{password}@{host}:{port}/{db_name}')
                env_content = self.update_env_var(env_content, 'DB_ENGINE', 'django.db.backends.postgresql')
                env_content = self.update_env_var(env_content, 'DB_NAME', db_name)
                env_content = self.update_env_var(env_content, 'DB_USER', user)
                env_content = self.update_env_var(env_content, 'DB_PASSWORD', password)
                env_content = self.update_env_var(env_content, 'DB_HOST', host)
                env_content = self.update_env_var(env_content, 'DB_PORT', port)
                
            elif db_type == 'mysql':
                db_name = config.get('name', config.get('NAME', 'fireflies'))
                host = config.get('host', config.get('HOST', 'localhost'))
                port = config.get('port', config.get('PORT', '3306'))
                user = config.get('user', config.get('USER', 'root'))
                password = config.get('password', config.get('PASSWORD', ''))
                
                env_content = self.update_env_var(env_content, 'DATABASE_URL', f'mysql://{user}:{password}@{host}:{port}/{db_name}')
                env_content = self.update_env_var(env_content, 'DB_ENGINE', 'django.db.backends.mysql')
                env_content = self.update_env_var(env_content, 'DB_NAME', db_name)
                env_content = self.update_env_var(env_content, 'DB_USER', user)
                env_content = self.update_env_var(env_content, 'DB_PASSWORD', password)
                env_content = self.update_env_var(env_content, 'DB_HOST', host)
                env_content = self.update_env_var(env_content, 'DB_PORT', port)
            
            # Salvar arquivo .env
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(env_content)
            
            logger.info(f"Configuração de banco aplicada: {db_type} - {db_name}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao aplicar configuração de banco: {e}", exc_info=True)
            return False
    
    def apply_admin_config(self, config):
        """Aplica configuração do administrador"""
        try:
            from django.contrib.auth import get_user_model
            from django.contrib.auth.hashers import make_password

            User = get_user_model()

            # Validação obrigatória
            username = config.get('username')
            email = config.get('email')
            password = config.get('password')
            if not username or not password:
                logger.error(f"Dados obrigatórios ausentes para criação do admin: username={username}, password={'***' if password else ''}")
                return False

            # Verificar se o usuário já existe
            if User.objects.filter(username=username).exists():
                logger.warning(f"Usuário {username} já existe")
                return True

            if email and User.objects.filter(email=email).exists():
                logger.warning(f"Email {email} já existe")
                return True

            # Criar superusuário
            user = User.objects.create(
                username=username,
                email=email,
                password=make_password(password),
                first_name=config.get('first_name', ''),
                last_name=config.get('last_name', ''),
                is_staff=True,
                is_superuser=True,
                is_active=True
            )

            logger.info(f"Usuário administrador {username} criado com sucesso")
            return True

        except Exception as e:
            logger.error(f"Erro ao criar usuário administrador: {e}", exc_info=True)
            return False
    
    def apply_email_config(self, config):
        """Aplica configuração de email ao .env"""
        try:
            env_file = Path(settings.BASE_DIR) / '.env'
            
            # Ler arquivo .env atual
            env_content = ""
            if env_file.exists():
                with open(env_file, 'r', encoding='utf-8') as f:
                    env_content = f.read()
            
            # Handle both frontend format (lowercase) and backend format
            email_host = config.get('host', config.get('email_host', ''))
            email_port = config.get('port', config.get('email_port', ''))
            email_user = config.get('address', config.get('email_user', ''))
            email_password = config.get('password', config.get('email_password', ''))
            
            if email_host and email_port:
                # SMTP configuration
                env_content = self.update_env_var(env_content, 'EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
                env_content = self.update_env_var(env_content, 'EMAIL_HOST', email_host)
                env_content = self.update_env_var(env_content, 'EMAIL_PORT', email_port)
                env_content = self.update_env_var(env_content, 'EMAIL_HOST_USER', email_user)
                env_content = self.update_env_var(env_content, 'EMAIL_HOST_PASSWORD', email_password)
                env_content = self.update_env_var(env_content, 'EMAIL_USE_TLS', 'True')
                env_content = self.update_env_var(env_content, 'EMAIL_USE_SSL', 'False')
                env_content = self.update_env_var(env_content, 'DEFAULT_FROM_EMAIL', email_user)
            else:
                # Console backend for development
                env_content = self.update_env_var(env_content, 'EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
                env_content = self.update_env_var(env_content, 'EMAIL_HOST', '')
                env_content = self.update_env_var(env_content, 'EMAIL_PORT', '')
                env_content = self.update_env_var(env_content, 'EMAIL_HOST_USER', '')
                env_content = self.update_env_var(env_content, 'EMAIL_HOST_PASSWORD', '')
                env_content = self.update_env_var(env_content, 'EMAIL_USE_TLS', 'False')
                env_content = self.update_env_var(env_content, 'EMAIL_USE_SSL', 'False')
            
            # Salvar arquivo .env
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(env_content)
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao aplicar configuração de email: {e}", exc_info=True)
            return False
    
    def apply_security_config(self, config):
        """Aplica configuração de segurança ao .env"""
        try:
            env_file = Path(settings.BASE_DIR) / '.env'
            
            # Ler arquivo .env atual
            env_content = ""
            if env_file.exists():
                with open(env_file, 'r', encoding='utf-8') as f:
                    env_content = f.read()
            
            # Handle both frontend format (lowercase) and backend format
            debug_mode = config.get('debug_mode', 'True')
            secret_key = config.get('secret_key', '')
            
            # Set debug mode
            env_content = self.update_env_var(env_content, 'DEBUG', debug_mode)
            
            # Set secret key if provided
            if secret_key:
                env_content = self.update_env_var(env_content, 'SECRET_KEY', secret_key)
            
            # For now, use development-friendly settings
            env_content = self.update_env_var(env_content, 'ALLOWED_HOSTS', '*')
            env_content = self.update_env_var(env_content, 'CSRF_TRUSTED_ORIGINS', '')
            env_content = self.update_env_var(env_content, 'SECURE_SSL_REDIRECT', 'False')
            env_content = self.update_env_var(env_content, 'SESSION_COOKIE_SECURE', 'False')
            env_content = self.update_env_var(env_content, 'CSRF_COOKIE_SECURE', 'False')
            
            # Salvar arquivo .env
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(env_content)
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao aplicar configuração de segurança: {e}", exc_info=True)
            return False
    
    def update_env_var(self, env_content: str, var_name: str, var_value: str) -> str:
        """Atualiza ou adiciona uma variável no arquivo .env"""
        lines = env_content.split('\n')
        var_found = False
        
        # Procurar pela variável existente
        for i, line in enumerate(lines):
            if line.strip().startswith(f'{var_name}='):
                lines[i] = f'{var_name}={var_value}'
                var_found = True
                break
        
        # Se não encontrou, adicionar no final
        if not var_found:
            lines.append(f'{var_name}={var_value}')
        
        return '\n'.join(lines) 