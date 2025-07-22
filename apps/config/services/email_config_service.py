from django.conf import settings
from django.core.mail import get_connection
from apps.config.models import EmailConfiguration
from apps.config.repositories.config_repository import DjangoSystemConfigRepository
from apps.config.interfaces.services import IEmailConfigService
from apps.config.interfaces.repositories import ISystemConfigRepository
from django.contrib.auth import get_user_model
import logging
import os

User = get_user_model()
logger = logging.getLogger(__name__)


class DynamicEmailConfigService(IEmailConfigService):
    """Serviço para gerenciar configurações de email dinamicamente com aplicação em tempo real"""
    
    def __init__(self, config_repository: ISystemConfigRepository = None):
        self.current_config = None
        self.connection = None
        # Usa injeção de dependência para o repositório
        self.config_repository = config_repository or DjangoSystemConfigRepository()
    
    def get_active_config(self):
        """Retorna a configuração de email ativa do banco ou sistema"""
        try:
            # Primeiro tenta buscar do repositório de configurações
            try:
                config_value = self.config_repository.get_by_key('email_settings')
                if config_value:
                    return config_value
            except Exception:
                pass  # Configuração não existe no banco, usa fallback

            # Fallback para modelo EmailConfiguration
            email_config = EmailConfiguration.objects.filter(is_active=True).first()
            if email_config:
                return email_config.get_config_dict()

            # Último fallback para settings.py
            return self._get_settings_config()

        except Exception as e:
            logger.error(f'Erro ao obter configuração de email: {e}')
            return self._get_settings_config()
    
    def _get_settings_config(self):
        """Retorna configurações padrão do settings.py"""
        return {
            'EMAIL_BACKEND': getattr(settings, 'EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend'),
            'EMAIL_HOST': getattr(settings, 'EMAIL_HOST', ''),
            'EMAIL_PORT': getattr(settings, 'EMAIL_PORT', 587),
            'EMAIL_HOST_USER': getattr(settings, 'EMAIL_HOST_USER', ''),
            'EMAIL_HOST_PASSWORD': getattr(settings, 'EMAIL_HOST_PASSWORD', ''),
            'EMAIL_USE_TLS': getattr(settings, 'EMAIL_USE_TLS', True),
            'EMAIL_USE_SSL': getattr(settings, 'EMAIL_USE_SSL', False),
            'DEFAULT_FROM_EMAIL': getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@havoc.com'),
            'EMAIL_TIMEOUT': getattr(settings, 'EMAIL_TIMEOUT', 30),
        }
    
    def get_connection(self, config=None):
        """Cria conexão de email com configurações específicas"""
        if config is None:
            config = self.get_active_config()
        
        return get_connection(
            backend=config['EMAIL_BACKEND'],
            host=config.get('EMAIL_HOST', ''),
            port=config.get('EMAIL_PORT', 587),
            username=config.get('EMAIL_HOST_USER', ''),
            password=config.get('EMAIL_HOST_PASSWORD', ''),
            use_tls=config.get('EMAIL_USE_TLS', True),
            use_ssl=config.get('EMAIL_USE_SSL', False),
            timeout=config.get('EMAIL_TIMEOUT', 30),
        )
    
    def test_connection(self, config=None):
        """Testa a conexão de email"""
        try:
            if config is None:
                config = self.get_active_config()
            
            # Se for backend de console/dummy, considera como válido
            backend = config.get('EMAIL_BACKEND', '')
            if 'console' in backend or 'dummy' in backend or 'locmem' in backend:
                return True, "Backend de desenvolvimento configurado corretamente!"
            
            # Para SMTP, testa a conexão real
            connection = self.get_connection(config)
            connection.open()
            connection.close()
            return True, "Conexão SMTP estabelecida com sucesso!"
            
        except Exception as e:
            logger.error(f'Erro ao testar conexão de email: {e}')
            return False, str(e)
    
    def apply_config_to_settings(self, config_dict):
        """Aplica configurações dinamicamente ao Django settings"""
        try:
            # Atualiza as configurações do Django em tempo de execução
            settings.EMAIL_BACKEND = config_dict['EMAIL_BACKEND']
            settings.EMAIL_HOST = config_dict.get('EMAIL_HOST', '')
            settings.EMAIL_PORT = config_dict.get('EMAIL_PORT', 587)
            settings.EMAIL_HOST_USER = config_dict.get('EMAIL_HOST_USER', '')
            settings.EMAIL_HOST_PASSWORD = config_dict.get('EMAIL_HOST_PASSWORD', '')
            settings.EMAIL_USE_TLS = config_dict.get('EMAIL_USE_TLS', True)
            settings.EMAIL_USE_SSL = config_dict.get('EMAIL_USE_SSL', False)
            settings.DEFAULT_FROM_EMAIL = config_dict.get('DEFAULT_FROM_EMAIL', 'noreply@havoc.com')
            settings.EMAIL_TIMEOUT = config_dict.get('EMAIL_TIMEOUT', 30)
            
            # Também atualiza variáveis de ambiente para persistência
            self._update_environment_variables(config_dict)
            
            logger.info('Configurações de email aplicadas dinamicamente')
            return True
            
        except Exception as e:
            logger.error(f'Erro ao aplicar configurações de email: {e}')
            return False
    
    def _update_environment_variables(self, config_dict):
        """Atualiza variáveis de ambiente (para persistência entre reinicializações)"""
        try:
            env_mapping = {
                'EMAIL_BACKEND': 'EMAIL_BACKEND',
                'EMAIL_HOST': 'EMAIL_HOST',
                'EMAIL_PORT': 'EMAIL_PORT',
                'EMAIL_HOST_USER': 'EMAIL_HOST_USER',
                'EMAIL_HOST_PASSWORD': 'EMAIL_HOST_PASSWORD',
                'EMAIL_USE_TLS': 'EMAIL_USE_TLS',
                'EMAIL_USE_SSL': 'EMAIL_USE_SSL',
                'DEFAULT_FROM_EMAIL': 'DEFAULT_FROM_EMAIL',
                'EMAIL_TIMEOUT': 'EMAIL_TIMEOUT',
            }

            # Atualiza variáveis na memória
            for config_key, env_key in env_mapping.items():
                value = config_dict.get(config_key, '')
                if isinstance(value, bool):
                    value = 'True' if value else 'False'
                elif value is None:
                    value = ''
                os.environ[env_key] = str(value)

            # Atualiza arquivo .env
            self._update_env_file(config_dict, env_mapping)

            logger.info('Variáveis de ambiente de email atualizadas (memória e arquivo .env)')

        except Exception as e:
            logger.error(f'Erro ao atualizar variáveis de ambiente: {e}')

    def _update_env_file(self, config_dict, env_mapping):
        """Atualiza o arquivo .env com as configurações de email usando python-dotenv."""
        try:
            from dotenv import find_dotenv, set_key

            # Encontra o arquivo .env na raiz do projeto
            env_path = find_dotenv()

            # Se o .env não existir, cria um
            if not env_path:
                from pathlib import Path
                from django.conf import settings
                env_path = Path(settings.BASE_DIR) / '.env'
                env_path.touch()
                logger.info("Arquivo .env não encontrado, um novo foi criado.")

            # Itera sobre o mapeamento e atualiza as chaves no arquivo .env
            for config_key, env_key in env_mapping.items():
                if config_key in config_dict:
                    value = config_dict[config_key]
                    
                    # Converte booleano para string
                    if isinstance(value, bool):
                        value = 'True' if value else 'False'
                    # Converte None para string vazia
                    elif value is None:
                        value = ''
                    
                    # Usa set_key para atualizar a variável de forma segura
                    set_key(env_path, env_key, str(value))

            logger.info(f'Arquivo .env atualizado com sucesso em: {env_path}')

        except Exception as e:
            logger.error(f'Erro ao atualizar arquivo .env com python-dotenv: {e}')
    
    def save_config(self, config_dict, user=None, description="Configuração de email"):
        """Salva configuração no repositório e aplica imediatamente"""
        try:
            # Salva no repositório de configurações (sistema antigo)
            success = self.config_repository.set_config(
                'email_settings', 
                config_dict, 
                description=description,
                updated_by=user
            )
            
            # Salva também no novo modelo EmailConfiguration
            self._save_to_email_configuration(config_dict, user, description)
            
            if success:
                # Aplica as configurações dinamicamente
                self.apply_config_to_settings(config_dict)
                
                # Força recarregamento das configurações
                self._reload_settings_from_env()
                
                logger.info(f'Configuração de email salva e aplicada por {user.email if user else "sistema"}')
                return True
            else:
                logger.error('Erro ao salvar configuração de email no repositório')
                return False
                
        except Exception as e:
            logger.error(f'Erro ao salvar configuração de email: {e}')
            return False
    
    def _save_to_email_configuration(self, config_dict, user=None, description="Configuração de email"):
        """Salva configuração no modelo EmailConfiguration"""
        try:
            # Desativa configurações padrão existentes
            EmailConfiguration.objects.filter(is_default=True).update(is_default=False)
            
            # Cria ou atualiza a configuração padrão
            email_config, created = EmailConfiguration.objects.get_or_create(
                is_default=True,
                defaults={
                    'name': 'Configuração Padrão',
                    'description': description,
                    'email_backend': config_dict.get('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend'),
                    'email_host': config_dict.get('EMAIL_HOST', ''),
                    'email_port': config_dict.get('EMAIL_PORT', 587),
                    'email_host_user': config_dict.get('EMAIL_HOST_USER', ''),
                    'email_host_password': config_dict.get('EMAIL_HOST_PASSWORD', ''),
                    'email_use_tls': config_dict.get('EMAIL_USE_TLS', True),
                    'email_use_ssl': config_dict.get('EMAIL_USE_SSL', False),
                    'default_from_email': config_dict.get('DEFAULT_FROM_EMAIL', 'noreply@havoc.com'),
                    'email_timeout': config_dict.get('EMAIL_TIMEOUT', 30),
                    'is_active': True,
                    'is_default': True,
                    'created_by': user,
                    'updated_by': user,
                }
            )
            
            if not created:
                # Atualiza configuração existente
                email_config.name = 'Configuração Padrão'
                email_config.description = description
                email_config.email_backend = config_dict.get('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
                email_config.email_host = config_dict.get('EMAIL_HOST', '')
                email_config.email_port = config_dict.get('EMAIL_PORT', 587)
                email_config.email_host_user = config_dict.get('EMAIL_HOST_USER', '')
                email_config.email_host_password = config_dict.get('EMAIL_HOST_PASSWORD', '')
                email_config.email_use_tls = config_dict.get('EMAIL_USE_TLS', True)
                email_config.email_use_ssl = config_dict.get('EMAIL_USE_SSL', False)
                email_config.default_from_email = config_dict.get('DEFAULT_FROM_EMAIL', 'noreply@havoc.com')
                email_config.email_timeout = config_dict.get('EMAIL_TIMEOUT', 30)
                email_config.is_active = True
                email_config.updated_by = user
                email_config.save()
            
            logger.info(f'Configuração salva no modelo EmailConfiguration: {email_config.name}')
            return True
            
        except Exception as e:
            logger.error(f'Erro ao salvar no modelo EmailConfiguration: {e}')
            return False
    
    def _reload_settings_from_env(self):
        """Recarrega as configurações de email do arquivo .env"""
        try:
            from dotenv import load_dotenv
            from pathlib import Path
            from django.conf import settings
            
            # Recarrega o arquivo .env
            env_path = Path(settings.BASE_DIR) / '.env'
            if env_path.exists():
                load_dotenv(env_path, override=True)
                
                # Reaplica as configurações do .env
                self._apply_env_to_settings()
                
                logger.info('Configurações de email recarregadas do arquivo .env')
                return True
            else:
                logger.warning('Arquivo .env não encontrado para recarregamento')
                return False
                
        except Exception as e:
            logger.error(f'Erro ao recarregar configurações do .env: {e}')
            return False
    
    def _apply_env_to_settings(self):
        """Aplica configurações do .env diretamente ao settings"""
        try:
            import os
            
            # Mapeamento das variáveis de ambiente para settings
            env_mapping = {
                'EMAIL_BACKEND': 'EMAIL_BACKEND',
                'EMAIL_HOST': 'EMAIL_HOST',
                'EMAIL_PORT': 'EMAIL_PORT',
                'EMAIL_HOST_USER': 'EMAIL_HOST_USER',
                'EMAIL_HOST_PASSWORD': 'EMAIL_HOST_PASSWORD',
                'EMAIL_USE_TLS': 'EMAIL_USE_TLS',
                'EMAIL_USE_SSL': 'EMAIL_USE_SSL',
                'DEFAULT_FROM_EMAIL': 'DEFAULT_FROM_EMAIL',
                'EMAIL_TIMEOUT': 'EMAIL_TIMEOUT',
            }
            
            # Aplica cada configuração
            for env_key, setting_key in env_mapping.items():
                value = os.environ.get(env_key)
                if value is not None:
                    if setting_key in ['EMAIL_PORT', 'EMAIL_TIMEOUT']:
                        try:
                            setattr(settings, setting_key, int(value))
                        except ValueError:
                            logger.warning(f'Valor inválido para {setting_key}: {value}')
                    elif setting_key in ['EMAIL_USE_TLS', 'EMAIL_USE_SSL']:
                        setattr(settings, setting_key, value.lower() == 'true')
                    else:
                        setattr(settings, setting_key, value)
            
            logger.info('Configurações de email aplicadas do .env para settings')
            return True
            
        except Exception as e:
            logger.error(f'Erro ao aplicar configurações do .env: {e}')
            return False
    
    def sync_config_to_env(self):
        """Sincroniza configuração do banco para variáveis de ambiente"""
        try:
            config = self.get_active_config()
            if config:
                self._update_environment_variables(config)
                logger.info('Configuração de email sincronizada com variáveis de ambiente')
                return True
            else:
                logger.warning('Nenhuma configuração de email ativa encontrada')
                return False
                
        except Exception as e:
            logger.error(f'Erro ao sincronizar configuração de email: {e}')
            return False
    
    def get_backend_info(self, backend_name):
        """Retorna informações sobre um backend específico"""
        backends = {
            'django.core.mail.backends.smtp.EmailBackend': {
                'name': 'SMTP',
                'description': 'Envio via servidor SMTP',
                'fields': ['EMAIL_HOST', 'EMAIL_PORT', 'EMAIL_HOST_USER', 'EMAIL_HOST_PASSWORD'],
                'optional_fields': ['EMAIL_USE_TLS', 'EMAIL_USE_SSL', 'EMAIL_TIMEOUT'],
                'defaults': {
                    'EMAIL_PORT': 587,
                    'EMAIL_USE_TLS': True,
                    'EMAIL_USE_SSL': False,
                    'EMAIL_TIMEOUT': 30
                }
            },
            'django.core.mail.backends.console.EmailBackend': {
                'name': 'Console',
                'description': 'Exibe emails no console (desenvolvimento)',
                'fields': [],
                'optional_fields': [],
                'defaults': {}
            },
            'django.core.mail.backends.filebased.EmailBackend': {
                'name': 'Arquivo',
                'description': 'Salva emails em arquivos',
                'fields': ['EMAIL_FILE_PATH'],
                'optional_fields': [],
                'defaults': {}
            },
            'django.core.mail.backends.locmem.EmailBackend': {
                'name': 'Memória Local',
                'description': 'Armazena emails na memória (desenvolvimento)',
                'fields': [],
                'optional_fields': [],
                'defaults': {}
            }
        }
        
        return backends.get(backend_name, {
            'name': 'Desconhecido',
            'description': 'Backend não reconhecido',
            'fields': [],
            'optional_fields': [],
            'defaults': {}
        })
    
    def get_preset_configs(self):
        """Retorna configurações pré-definidas para provedores populares"""
        return {
            'gmail': {
                'EMAIL_BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
                'EMAIL_HOST': 'smtp.gmail.com',
                'EMAIL_PORT': 587,
                'EMAIL_USE_TLS': True,
                'EMAIL_USE_SSL': False,
                'DEFAULT_FROM_EMAIL': 'seu-email@gmail.com',
                'description': 'Gmail SMTP'
            },
            'outlook': {
                'EMAIL_BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
                'EMAIL_HOST': 'smtp-mail.outlook.com',
                'EMAIL_PORT': 587,
                'EMAIL_USE_TLS': True,
                'EMAIL_USE_SSL': False,
                'DEFAULT_FROM_EMAIL': 'seu-email@outlook.com',
                'description': 'Outlook/Hotmail SMTP'
            },
            'yahoo': {
                'EMAIL_BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
                'EMAIL_HOST': 'smtp.mail.yahoo.com',
                'EMAIL_PORT': 587,
                'EMAIL_USE_TLS': True,
                'EMAIL_USE_SSL': False,
                'DEFAULT_FROM_EMAIL': 'seu-email@yahoo.com',
                'description': 'Yahoo Mail SMTP'
            },
            'sendgrid': {
                'EMAIL_BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
                'EMAIL_HOST': 'smtp.sendgrid.net',
                'EMAIL_PORT': 587,
                'EMAIL_USE_TLS': True,
                'EMAIL_USE_SSL': False,
                'DEFAULT_FROM_EMAIL': 'noreply@seudominio.com',
                'description': 'SendGrid SMTP'
            },
            'amazon_ses': {
                'EMAIL_BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
                'EMAIL_HOST': 'email-smtp.us-east-1.amazonaws.com',
                'EMAIL_PORT': 587,
                'EMAIL_USE_TLS': True,
                'EMAIL_USE_SSL': False,
                'DEFAULT_FROM_EMAIL': 'noreply@seudominio.com',
                'description': 'Amazon SES SMTP'
            },
            'console': {
                'EMAIL_BACKEND': 'django.core.mail.backends.console.EmailBackend',
                'DEFAULT_FROM_EMAIL': 'noreply@localhost',
                'description': 'Console (desenvolvimento)'
            },
            'file': {
                'EMAIL_BACKEND': 'django.core.mail.backends.filebased.EmailBackend',
                'EMAIL_FILE_PATH': '/tmp/django-mails',
                'DEFAULT_FROM_EMAIL': 'noreply@localhost',
                'description': 'Arquivo (desenvolvimento)'
            }
        }
