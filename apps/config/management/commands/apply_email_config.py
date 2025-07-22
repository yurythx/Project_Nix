from django.core.management.base import BaseCommand
from django.conf import settings
from apps.config.services.email_config_service import DynamicEmailConfigService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Aplica configurações de email do banco de dados às variáveis de ambiente'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força a aplicação mesmo se não houver configurações no banco',
        )
        parser.add_argument(
            '--show-current',
            action='store_true',
            help='Mostra as configurações atuais sem aplicar',
        )
        parser.add_argument(
            '--test-connection',
            action='store_true',
            help='Testa a conexão após aplicar as configurações',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('📧 APLICAÇÃO DE CONFIGURAÇÕES DE EMAIL')
        )
        self.stdout.write('=' * 50)
        
        email_service = DynamicEmailConfigService()
        
        # Mostra configurações atuais se solicitado
        if options.get('show_current'):
            self._show_current_config(email_service)
            return
        
        try:
            # Obtém configurações ativas
            current_config = email_service.get_active_config()
            
            if not current_config:
                if not options.get('force'):
                    self.stdout.write(
                        self.style.WARNING(
                            '⚠️  Nenhuma configuração de email encontrada no banco.\n'
                            'Use --force para aplicar configurações padrão.'
                        )
                    )
                    return
                else:
                    self.stdout.write(
                        self.style.WARNING('🔧 Aplicando configurações padrão...')
                    )
            
            # Aplica configurações
            self.stdout.write('📝 Aplicando configurações de email...')
            success = email_service.apply_config_to_settings(current_config)
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS('✅ Configurações aplicadas com sucesso!')
                )
                
                # Mostra configurações aplicadas
                self._show_applied_config(current_config)
                
                # Testa conexão se solicitado
                if options.get('test_connection'):
                    self._test_connection(email_service)
                    
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Falha ao aplicar configurações')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro inesperado: {str(e)}')
            )
            logger.error(f'Erro ao aplicar configurações de email: {e}', exc_info=True)
    
    def _show_current_config(self, email_service):
        """Mostra as configurações atuais"""
        self.stdout.write('\n📋 CONFIGURAÇÕES ATUAIS:')
        self.stdout.write('-' * 30)
        
        current_config = email_service.get_active_config()
        
        if current_config:
            backend = current_config.get('EMAIL_BACKEND', 'Não configurado')
            backend_info = email_service.get_backend_info(backend)
            
            self.stdout.write(f'Backend: {backend_info["name"]}')
            self.stdout.write(f'Descrição: {backend_info["description"]}')
            
            if backend_info.get('requires_config', False):
                self.stdout.write(f'Host: {current_config.get("EMAIL_HOST", "Não configurado")}')
                self.stdout.write(f'Porta: {current_config.get("EMAIL_PORT", "Não configurado")}')
                self.stdout.write(f'Usuário: {current_config.get("EMAIL_HOST_USER", "Não configurado")}')
                self.stdout.write(f'TLS: {"Sim" if current_config.get("EMAIL_USE_TLS") else "Não"}')
                self.stdout.write(f'SSL: {"Sim" if current_config.get("EMAIL_USE_SSL") else "Não"}')
            
            self.stdout.write(f'Email padrão: {current_config.get("DEFAULT_FROM_EMAIL", "Não configurado")}')
        else:
            self.stdout.write('❌ Nenhuma configuração encontrada')
    
    def _show_applied_config(self, config):
        """Mostra as configurações que foram aplicadas"""
        self.stdout.write('\n📊 CONFIGURAÇÕES APLICADAS:')
        self.stdout.write('-' * 35)
        
        backend = config.get('EMAIL_BACKEND', 'Não configurado')
        self.stdout.write(f'Backend: {backend}')
        
        if 'smtp' in backend.lower():
            self.stdout.write(f'Host: {config.get("EMAIL_HOST", "Não configurado")}')
            self.stdout.write(f'Porta: {config.get("EMAIL_PORT", "Não configurado")}')
            self.stdout.write(f'Usuário: {config.get("EMAIL_HOST_USER", "Não configurado")}')
            self.stdout.write(f'TLS: {"Ativado" if config.get("EMAIL_USE_TLS") else "Desativado"}')
            self.stdout.write(f'SSL: {"Ativado" if config.get("EMAIL_USE_SSL") else "Desativado"}')
        elif 'console' in backend.lower():
            self.stdout.write('📺 Modo desenvolvimento - emails no console')
        elif 'dummy' in backend.lower():
            self.stdout.write('🚫 Modo desabilitado - emails não serão enviados')
        
        self.stdout.write(f'Email padrão: {config.get("DEFAULT_FROM_EMAIL", "Não configurado")}')
        self.stdout.write(f'Timeout: {config.get("EMAIL_TIMEOUT", 30)} segundos')
    
    def _test_connection(self, email_service):
        """Testa a conexão de email"""
        self.stdout.write('\n🔌 TESTANDO CONEXÃO:')
        self.stdout.write('-' * 25)
        
        try:
            success, message = email_service.test_connection()
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ {message}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ {message}')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro no teste: {str(e)}')
            )
    
    def _show_environment_variables(self):
        """Mostra as variáveis de ambiente relacionadas ao email"""
        self.stdout.write('\n🌍 VARIÁVEIS DE AMBIENTE:')
        self.stdout.write('-' * 30)
        
        env_vars = [
            'DJANGO_EMAIL_BACKEND',
            'DJANGO_EMAIL_HOST',
            'DJANGO_EMAIL_PORT',
            'DJANGO_EMAIL_HOST_USER',
            'DJANGO_EMAIL_USE_TLS',
            'DJANGO_EMAIL_USE_SSL',
            'DJANGO_DEFAULT_FROM_EMAIL',
        ]
        
        import os
        for var in env_vars:
            value = os.environ.get(var, 'Não definida')
            # Oculta senhas
            if 'PASSWORD' in var and value != 'Não definida':
                value = '*' * len(value)
            self.stdout.write(f'{var}: {value}')
    
    def _create_sample_config(self):
        """Cria uma configuração de exemplo"""
        self.stdout.write('\n📝 CRIANDO CONFIGURAÇÃO DE EXEMPLO:')
        self.stdout.write('-' * 40)
        
        sample_config = {
            'EMAIL_BACKEND': 'django.core.mail.backends.console.EmailBackend',
            'EMAIL_HOST': '',
            'EMAIL_PORT': 587,
            'EMAIL_HOST_USER': '',
            'EMAIL_HOST_PASSWORD': '',
            'EMAIL_USE_TLS': True,
            'EMAIL_USE_SSL': False,
            'DEFAULT_FROM_EMAIL': 'noreply@havoc.com',
            'EMAIL_TIMEOUT': 30,
        }
        
        email_service = DynamicEmailConfigService()
        success = email_service.save_config(
            config_dict=sample_config,
            description='Configuração de exemplo criada via comando'
        )
        
        if success:
            self.stdout.write(
                self.style.SUCCESS('✅ Configuração de exemplo criada!')
            )
        else:
            self.stdout.write(
                self.style.ERROR('❌ Falha ao criar configuração de exemplo')
            )
