"""
Comando para sincronizar configurações de email do banco para o arquivo .env.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.config.services.email_config_service import DynamicEmailConfigService
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sincroniza configurações de email do banco de dados para o arquivo .env'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força a sincronização mesmo se houver conflitos',
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Username do usuário que está executando a sincronização',
        )

    def handle(self, *args, **options):
        try:
            # Obter usuário se especificado
            user = None
            if options['user']:
                try:
                    user = User.objects.get(username=options['user'])
                except User.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'Usuário "{options["user"]}" não encontrado')
                    )

            # Inicializar serviço
            email_service = DynamicEmailConfigService()
            
            # Obter configuração atual
            current_config = email_service.get_active_config()
            
            if not current_config:
                self.stdout.write(
                    self.style.WARNING('Nenhuma configuração de email ativa encontrada')
                )
                return

            self.stdout.write('🔄 Sincronizando configurações de email...')
            
            # Sincronizar configuração
            success = email_service.sync_config_to_env()
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS('✅ Configurações de email sincronizadas com sucesso!')
                )
                
                # Mostrar configurações aplicadas
                self.stdout.write('\n📧 Configurações aplicadas:')
                for key, value in current_config.items():
                    if key == 'EMAIL_HOST_PASSWORD':
                        self.stdout.write(f'  {key}: {"*" * len(str(value)) if value else "não definida"}')
                    else:
                        self.stdout.write(f'  {key}: {value}')
                
                self.stdout.write(
                    '\n💡 Para aplicar completamente, reinicie o servidor Django.'
                )
                
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Erro ao sincronizar configurações de email')
                )

        except Exception as e:
            logger.error(f'Erro ao sincronizar configurações de email: {e}', exc_info=True)
            self.stdout.write(
                self.style.ERROR(f'❌ Erro inesperado: {str(e)}')
            ) 