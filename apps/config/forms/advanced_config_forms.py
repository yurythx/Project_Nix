from django import forms
from django.core.validators import MinLengthValidator
from django.conf import settings
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Row, Column, Submit, Reset, HTML, Div
from crispy_forms.bootstrap import FormActions
from apps.config.models import SystemConfiguration
from apps.config.services.system_config_service import SystemConfigService
from apps.config.repositories.config_repository import DjangoSystemConfigRepository, DjangoAuditLogRepository
import json
import os


class DatabaseConfigForm(forms.Form):
    """Formulário para configurações de banco de dados"""
    
    # Configurações principais
    engine = forms.ChoiceField(
        label='Engine do Banco',
        choices=[
            ('django.db.backends.postgresql', 'PostgreSQL'),
            ('django.db.backends.mysql', 'MySQL'),
            ('django.db.backends.sqlite3', 'SQLite'),
            ('django.db.backends.oracle', 'Oracle'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    name = forms.CharField(
        label='Nome do Banco',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'nome_do_banco'
        })
    )
    
    user = forms.CharField(
        label='Usuário',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'usuario_db'
        })
    )
    
    password = forms.CharField(
        label='Senha',
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••'
        })
    )
    
    host = forms.CharField(
        label='Host',
        max_length=100,
        required=False,
        initial='localhost',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'localhost'
        })
    )
    
    port = forms.CharField(
        label='Porta',
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '5432'
        })
    )
    
    # Opções avançadas
    conn_max_age = forms.IntegerField(
        label='Tempo de Vida da Conexão (segundos)',
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0'
        })
    )
    
    atomic_requests = forms.BooleanField(
        label='Requisições Atômicas',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    autocommit = forms.BooleanField(
        label='Auto Commit',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Carrega configurações atuais
        self.load_current_config()
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'needs-validation'
        self.helper.attrs = {'novalidate': ''}
        
        self.helper.layout = Layout(
            Fieldset(
                'Configurações Principais do Banco de Dados',
                Row(
                    Column('engine', css_class='col-md-6'),
                    Column('name', css_class='col-md-6'),
                ),
                Row(
                    Column('user', css_class='col-md-6'),
                    Column('password', css_class='col-md-6'),
                ),
                Row(
                    Column('host', css_class='col-md-6'),
                    Column('port', css_class='col-md-6'),
                ),
                css_class='mb-4'
            ),
            
            Fieldset(
                'Configurações Avançadas',
                Row(
                    Column('conn_max_age', css_class='col-md-4'),
                    Column('atomic_requests', css_class='col-md-4'),
                    Column('autocommit', css_class='col-md-4'),
                ),
                css_class='mb-4'
            ),
            
            HTML('''
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>Atenção:</strong> Alterar as configurações do banco de dados pode afetar o funcionamento do sistema. 
                    Certifique-se de que as configurações estão corretas antes de salvar.
                </div>
            '''),
            
            FormActions(
                Submit('submit', 'Salvar Configurações', css_class='btn btn-primary btn-lg'),
                Reset('reset', 'Restaurar', css_class='btn btn-outline-secondary btn-lg'),
                HTML('<a href="{% url \'config:system_config\' %}" class="btn btn-outline-danger btn-lg">Cancelar</a>'),
                css_class='d-flex justify-content-between'
            )
        )

    def load_current_config(self):
        """Carrega configurações atuais do banco"""
        try:
            from apps.config.services.system_config_service import AuditLogService
            config_service = SystemConfigService(
                DjangoSystemConfigRepository(),
                AuditLogService(DjangoAuditLogRepository())
            )
            
            db_config = config_service.get_config('database_settings')
            if db_config and isinstance(db_config, dict):
                for field_name, value in db_config.items():
                    if field_name in self.fields:
                        self.fields[field_name].initial = value
        except:
            # Se não existir configuração, usa valores padrão
            pass

    def save(self, user=None):
        """Salva as configurações do banco de dados"""
        if not self.is_valid():
            return False

        try:
            from apps.config.services.system_config_service import AuditLogService
            config_service = SystemConfigService(
                DjangoSystemConfigRepository(),
                AuditLogService(DjangoAuditLogRepository())
            )
            
            db_config = {
                'ENGINE': self.cleaned_data['engine'],
                'NAME': self.cleaned_data['name'],
                'USER': self.cleaned_data.get('user', ''),
                'PASSWORD': self.cleaned_data.get('password', ''),
                'HOST': self.cleaned_data.get('host', 'localhost'),
                'PORT': self.cleaned_data.get('port', ''),
                'OPTIONS': {
                    'CONN_MAX_AGE': self.cleaned_data.get('conn_max_age', 0),
                    'ATOMIC_REQUESTS': self.cleaned_data.get('atomic_requests', False),
                    'AUTOCOMMIT': self.cleaned_data.get('autocommit', True),
                }
            }
            
            return config_service.set_config(
                key='database_settings',
                value=db_config,
                description='Configurações do banco de dados',
                updated_by=user
            )
        except Exception as e:
            self.add_error(None, f'Erro ao salvar configurações: {str(e)}')
            return False


class EmailConfigForm(forms.Form):
    """Formulário para configurações de email com aplicação dinâmica"""

    # Configurações SMTP
    email_backend = forms.ChoiceField(
        label='Modo de Operação',
        choices=[
            ('django.core.mail.backends.smtp.EmailBackend', '🚀 Produção (SMTP)'),
            ('django.core.mail.backends.console.EmailBackend', '🔧 Desenvolvimento (Console)'),
            ('django.core.mail.backends.filebased.EmailBackend', '📁 Arquivo Local'),
            ('django.core.mail.backends.locmem.EmailBackend', '🧪 Memória (Teste)'),
            ('django.core.mail.backends.dummy.EmailBackend', '❌ Desabilitado'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'onchange': 'toggleEmailFields(this.value)'
        }),
        help_text='Selecione o modo de operação do sistema de email'
    )
    
    email_host = forms.CharField(
        label='Servidor SMTP',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'smtp.gmail.com'
        })
    )
    
    email_port = forms.IntegerField(
        label='Porta SMTP',
        initial=587,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '65535'
        })
    )
    
    email_host_user = forms.CharField(
        label='Usuário SMTP',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'seu-email@gmail.com'
        })
    )
    
    email_host_password = forms.CharField(
        label='Senha SMTP',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••'
        })
    )
    
    email_use_tls = forms.BooleanField(
        label='Usar TLS',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    email_use_ssl = forms.BooleanField(
        label='Usar SSL',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    # Configurações de envio
    default_from_email = forms.EmailField(
        label='Email Padrão de Envio',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'noreply@seusite.com'
        })
    )
    
    server_email = forms.EmailField(
        label='Email do Servidor',
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'admin@seusite.com'
        })
    )
    
    email_timeout = forms.IntegerField(
        label='Timeout (segundos)',
        required=False,
        initial=30,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Carrega configurações atuais
        self.load_current_config()
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'needs-validation'
        self.helper.attrs = {'novalidate': ''}
        
        self.helper.layout = Layout(
            Fieldset(
                'Configurações do Servidor SMTP',
                'email_backend',
                Row(
                    Column('email_host', css_class='col-md-8'),
                    Column('email_port', css_class='col-md-4'),
                ),
                Row(
                    Column('email_host_user', css_class='col-md-6'),
                    Column('email_host_password', css_class='col-md-6'),
                ),
                Row(
                    Column('email_use_tls', css_class='col-md-4'),
                    Column('email_use_ssl', css_class='col-md-4'),
                    Column('email_timeout', css_class='col-md-4'),
                ),
                css_class='mb-4'
            ),
            
            Fieldset(
                'Configurações de Envio',
                Row(
                    Column('default_from_email', css_class='col-md-6'),
                    Column('server_email', css_class='col-md-6'),
                ),
                css_class='mb-4'
            ),
            
            HTML('''
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    <strong>Dica:</strong> Para Gmail, use smtp.gmail.com na porta 587 com TLS ativado.
                    Você pode precisar gerar uma senha de app específica.
                </div>
            '''),

            HTML('''
                <div class="alert alert-success">
                    <i class="fas fa-sync me-2"></i>
                    <strong>Integração com .env:</strong> As configurações serão salvas no banco de dados
                    e automaticamente sincronizadas com o arquivo .env para persistência.
                </div>
            '''),
            
            FormActions(
                Submit('submit', 'Salvar Configurações', css_class='btn btn-primary btn-lg'),
                Submit('test', 'Testar Configurações', css_class='btn btn-outline-info btn-lg'),
                Reset('reset', 'Restaurar', css_class='btn btn-outline-secondary btn-lg'),
                css_class='d-flex justify-content-between'
            )
        )

    def load_current_config(self):
        """Carrega configurações atuais de email"""
        try:
            from apps.config.services.email_config_service import DynamicEmailConfigService
            email_service = DynamicEmailConfigService()

            current_config = email_service.get_active_config()
            if current_config:
                # Mapeia as chaves do config para os campos do formulário
                field_mapping = {
                    'EMAIL_BACKEND': 'email_backend',
                    'EMAIL_HOST': 'email_host',
                    'EMAIL_PORT': 'email_port',
                    'EMAIL_HOST_USER': 'email_host_user',
                    'EMAIL_HOST_PASSWORD': 'email_host_password',
                    'EMAIL_USE_TLS': 'email_use_tls',
                    'EMAIL_USE_SSL': 'email_use_ssl',
                    'DEFAULT_FROM_EMAIL': 'default_from_email',
                    'EMAIL_TIMEOUT': 'email_timeout',
                }

                for config_key, field_name in field_mapping.items():
                    if config_key in current_config and field_name in self.fields:
                        self.fields[field_name].initial = current_config[config_key]
        except Exception as e:
            pass

    def save(self, user=None):
        """Salva as configurações de email e aplica dinamicamente"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f'Iniciando save do formulário de email - usuário: {user.username if user else "None"}')
        
        if not self.is_valid():
            logger.error(f'Formulário inválido: {self.errors}')
            return False

        try:
            from apps.config.services.email_config_service import DynamicEmailConfigService
            email_service = DynamicEmailConfigService()

            email_config = {
                'EMAIL_BACKEND': self.cleaned_data['email_backend'],
                'EMAIL_HOST': self.cleaned_data['email_host'],
                'EMAIL_PORT': self.cleaned_data['email_port'],
                'EMAIL_HOST_USER': self.cleaned_data['email_host_user'],
                'EMAIL_HOST_PASSWORD': self.cleaned_data['email_host_password'],
                'EMAIL_USE_TLS': self.cleaned_data['email_use_tls'],
                'EMAIL_USE_SSL': self.cleaned_data['email_use_ssl'],
                'DEFAULT_FROM_EMAIL': self.cleaned_data['default_from_email'],
                'SERVER_EMAIL': self.cleaned_data.get('server_email', ''),
                'EMAIL_TIMEOUT': self.cleaned_data.get('email_timeout') or 30,
            }
            
            logger.info(f'Configuração montada: {email_config}')

            # Salva e aplica as configurações dinamicamente
            result = email_service.save_config(
                config_dict=email_config,
                user=user,
                description='Configurações de email SMTP'
            )
            
            logger.info(f'Resultado do save_config: {result}')
            return result
            
        except Exception as e:
            logger.error(f'Erro no save do formulário: {e}', exc_info=True)
            self.add_error(None, f'Erro ao salvar configurações: {str(e)}')
            return False

    def test_connection(self):
        """Testa a conexão de email com as configurações atuais"""
        if not self.is_valid():
            return False, "Formulário inválido"

        try:
            from apps.config.services.email_config_service import DynamicEmailConfigService
            email_service = DynamicEmailConfigService()

            # Monta configuração temporária para teste
            test_config = {
                'EMAIL_BACKEND': self.cleaned_data['email_backend'],
                'EMAIL_HOST': self.cleaned_data['email_host'],
                'EMAIL_PORT': self.cleaned_data['email_port'],
                'EMAIL_HOST_USER': self.cleaned_data['email_host_user'],
                'EMAIL_HOST_PASSWORD': self.cleaned_data['email_host_password'],
                'EMAIL_USE_TLS': self.cleaned_data['email_use_tls'],
                'EMAIL_USE_SSL': self.cleaned_data['email_use_ssl'],
                'DEFAULT_FROM_EMAIL': self.cleaned_data['default_from_email'],
                'EMAIL_TIMEOUT': self.cleaned_data.get('email_timeout', 30),
            }

            # Testa a conexão usando o serviço
            return email_service.test_connection(test_config)

        except Exception as e:
            return False, f"Erro na conexão: {str(e)}"


class EnvironmentVariablesForm(forms.Form):
    """Formulário para gerenciar variáveis de ambiente do arquivo .env"""

    # Campo para edição direta do .env
    env_content = forms.CharField(
        label='Conteúdo do arquivo .env',
        widget=forms.Textarea(attrs={
            'class': 'form-control font-monospace',
            'rows': 25,
            'style': 'font-size: 0.9rem; line-height: 1.4;',
            'placeholder': 'Carregando conteúdo do arquivo .env...'
        }),
        help_text='Edite diretamente o conteúdo do arquivo .env. Linhas começando com # são comentários.'
    )



    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Carrega conteúdo atual do .env
        self.load_env_content()

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'needs-validation'
        self.helper.attrs = {'novalidate': ''}

        self.helper.layout = Layout(
            HTML('''
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    <strong>Editor do arquivo .env:</strong> Edite diretamente as variáveis de ambiente do sistema.
                    As alterações serão aplicadas imediatamente após salvar.
                </div>
            '''),

            'env_content',

            HTML('''
                <div class="alert alert-warning mt-3">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>Atenção:</strong> Alterar variáveis de ambiente pode afetar o funcionamento do sistema.
                    Faça backup antes de alterar e teste em ambiente de desenvolvimento primeiro.
                </div>
            '''),

            FormActions(
                Submit('submit', 'Salvar Arquivo .env', css_class='btn btn-primary btn-lg'),
                Submit('backup', 'Fazer Backup', css_class='btn btn-outline-info btn-lg'),
                Reset('reset', 'Restaurar', css_class='btn btn-outline-secondary btn-lg'),
                css_class='d-flex justify-content-between'
            )
        )

    def load_env_content(self):
        """Carrega o conteúdo atual do arquivo .env"""
        try:
            from pathlib import Path
            from django.conf import settings

            # Caminho para o arquivo .env
            env_path = Path(settings.BASE_DIR) / '.env'

            if env_path.exists():
                with open(env_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.fields['env_content'].initial = content
            else:
                # Se não existe, cria um template básico
                template = self.get_env_template()
                self.fields['env_content'].initial = template

        except Exception as e:
            # Em caso de erro, mostra template básico
            template = self.get_env_template()
            self.fields['env_content'].initial = f"# Erro ao carregar .env: {str(e)}\n\n{template}"

    def get_env_template(self):
        """Retorna um template básico para o arquivo .env"""
        return """# =============================================================================
# CONFIGURAÇÕES DO PROJETO HAVOC
# =============================================================================

# Configurações básicas do Django
DJANGO_SECRET_KEY=django-insecure-dev-key-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,testserver
ENVIRONMENT=development

# Configurações de banco de dados
DATABASE_ENGINE=sqlite
DATABASE_NAME=db.sqlite3

# Configurações de email
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=noreply@havoc.com

# Configurações de segurança
CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False

# Configurações de cache
CACHE_BACKEND=django.core.cache.backends.locmem.LocMemCache
CACHE_LOCATION=unique-snowflake

# Configurações do site
SITE_NAME=Havoc
SITE_DESCRIPTION=Sistema de gerenciamento de conteúdo moderno
SITE_URL=http://127.0.0.1:8000

# Configurações personalizadas
ACTIVE_MODULES=accounts,config,pages,articles
DEFAULT_THEME=light
DEFAULT_LANGUAGE=pt-br
DEFAULT_TIMEZONE=America/Sao_Paulo
"""

    def clean_env_content(self):
        """Valida o conteúdo do arquivo .env"""
        content = self.cleaned_data.get('env_content', '')

        if not content.strip():
            raise forms.ValidationError('O conteúdo do arquivo .env não pode estar vazio.')

        # Validação básica das linhas
        lines = content.split('\n')
        errors = []

        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if '=' not in line:
                errors.append(f'Linha {i}: Formato inválido. Use NOME=valor')
                continue

            key, value = line.split('=', 1)
            key = key.strip()

            if not key:
                errors.append(f'Linha {i}: Nome da variável não pode estar vazio')
            elif ' ' in key:
                errors.append(f'Linha {i}: Nome da variável não pode conter espaços: "{key}"')

        if errors:
            raise forms.ValidationError(errors)

        return content

    def save(self, user=None):
        """Salva o conteúdo no arquivo .env"""
        if not self.is_valid():
            return False

        try:
            from pathlib import Path
            from django.conf import settings
            from datetime import datetime

            # Caminho para o arquivo .env
            env_path = Path(settings.BASE_DIR) / '.env'

            # Faz backup do arquivo atual se existir
            if env_path.exists():
                backup_path = Path(settings.BASE_DIR) / f'.env.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
                import shutil
                shutil.copy2(env_path, backup_path)

            # Salva o novo conteúdo
            content = self.cleaned_data['env_content']
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # Log da ação se possível
            try:
                from apps.config.services.system_config_service import AuditLogService
                from apps.config.repositories.config_repository import DjangoAuditLogRepository

                audit_service = AuditLogService(DjangoAuditLogRepository())
                audit_service.log_user_action(
                    user=user,
                    action='UPDATE_ENV_FILE',
                    description='Arquivo .env atualizado via interface web'
                )
            except:
                pass  # Se não conseguir fazer log, continua

            return True

        except Exception as e:
            self.add_error(None, f'Erro ao salvar arquivo .env: {str(e)}')
            return False

    def create_backup(self):
        """Cria backup do arquivo .env atual"""
        try:
            from pathlib import Path
            from django.conf import settings
            from datetime import datetime
            import shutil

            env_path = Path(settings.BASE_DIR) / '.env'

            if not env_path.exists():
                return False, "Arquivo .env não existe"

            backup_path = Path(settings.BASE_DIR) / f'.env.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            shutil.copy2(env_path, backup_path)

            return True, f"Backup criado: {backup_path.name}"

        except Exception as e:
            return False, f"Erro ao criar backup: {str(e)}"
