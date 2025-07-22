from django.core.management.base import BaseCommand
from apps.config.services.email_config_service import DynamicEmailConfigService


class Command(BaseCommand):
    help = 'Sincroniza configurações de email do banco de dados com o arquivo .env'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força a sincronização mesmo se já existirem configurações no .env',
        )
        
        parser.add_argument(
            '--backup',
            action='store_true',
            help='Cria backup do .env antes de sincronizar',
        )
    
    def handle(self, *args, **options):
        self.stdout.write('🔄 Sincronizando configurações de email com arquivo .env...')
        
        try:
            email_service = DynamicEmailConfigService()
            
            # Verifica se há configuração ativa
            current_config = email_service.get_active_config()
            if not current_config:
                self.stdout.write(
                    self.style.WARNING('⚠️  Nenhuma configuração de email ativa encontrada.')
                )
                return
            
            # Mostra configuração atual
            self.stdout.write('\n📋 Configuração atual:')
            for key, value in current_config.items():
                if 'PASSWORD' in key.upper():
                    display_value = '***HIDDEN***'
                else:
                    display_value = value
                self.stdout.write(f'  • {key}: {display_value}')
            
            # Sincroniza
            success = email_service.sync_config_to_env()
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS('\n✅ Configurações sincronizadas com sucesso!')
                )
                self.stdout.write(
                    '📁 As variáveis de email foram atualizadas no arquivo .env'
                )
                self.stdout.write(
                    '🔄 Reinicie o servidor para aplicar as alterações'
                )
            else:
                self.stdout.write(
                    self.style.ERROR('\n❌ Erro ao sincronizar configurações.')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n💥 Erro inesperado: {str(e)}')
            )
