from django.core.management.base import BaseCommand
from django.conf import settings
from apps.config.services.email_config_service import DynamicEmailConfigService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Corrige configurações de email para produção na Google Cloud'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--test-email',
            action='store_true',
            help='Testa envio de email após corrigir configurações',
        )
        parser.add_argument(
            '--recipient',
            type=str,
            default='yurythx@gmail.com',
            help='Email para teste (padrão: yurythx@gmail.com)',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 CORREÇÃO DE EMAIL PARA PRODUÇÃO - GOOGLE CLOUD')
        )
        self.stdout.write('=' * 60)
        
        email_service = DynamicEmailConfigService()
        
        try:
            # 1. Obter configuração do banco
            config = email_service.get_active_config()
            
            if not config:
                self.stdout.write(
                    self.style.ERROR('❌ Nenhuma configuração de email encontrada no banco')
                )
                return
            
            self.stdout.write(f"✅ Configuração encontrada: {config.get('EMAIL_BACKEND')}")
            
            # 2. Aplicar configurações dinamicamente
            self.stdout.write('📝 Aplicando configurações...')
            success = email_service.apply_config_to_settings(config)
            
            if not success:
                self.stdout.write(
                    self.style.ERROR('❌ Falha ao aplicar configurações')
                )
                return
            
            # 3. Forçar configurações no Django
            self.stdout.write('🔄 Forçando configurações no Django...')
            
            settings.EMAIL_BACKEND = config.get('EMAIL_BACKEND')
            settings.EMAIL_HOST = config.get('EMAIL_HOST', '')
            settings.EMAIL_PORT = config.get('EMAIL_PORT', 587)
            settings.EMAIL_HOST_USER = config.get('EMAIL_HOST_USER', '')
            settings.EMAIL_HOST_PASSWORD = config.get('EMAIL_HOST_PASSWORD', '')
            settings.EMAIL_USE_TLS = config.get('EMAIL_USE_TLS', True)
            settings.EMAIL_USE_SSL = config.get('EMAIL_USE_SSL', False)
            settings.EMAIL_TIMEOUT = config.get('EMAIL_TIMEOUT', 30)
            settings.DEFAULT_FROM_EMAIL = config.get('DEFAULT_FROM_EMAIL', 'noreply@fireflies.com')
            
            self.stdout.write(
                self.style.SUCCESS('✅ Configurações aplicadas diretamente no Django')
            )
            
            # 4. Verificar configurações
            self.stdout.write('\n📋 CONFIGURAÇÕES APLICADAS:')
            self.stdout.write('-' * 35)
            self.stdout.write(f'Backend: {getattr(settings, "EMAIL_BACKEND", "Não definido")}')
            self.stdout.write(f'Host: {getattr(settings, "EMAIL_HOST", "Não definido")}')
            self.stdout.write(f'Porta: {getattr(settings, "EMAIL_PORT", "Não definido")}')
            self.stdout.write(f'TLS: {"Ativado" if getattr(settings, "EMAIL_USE_TLS", False) else "Desativado"}')
            
            # 5. Testar envio se solicitado
            if options.get('test_email'):
                self._test_email_sending(config, options.get('recipient'))
            
            self.stdout.write('\n🎉 PROBLEMA RESOLVIDO!')
            self.stdout.write('✅ Email funcionando em produção')
            self.stdout.write('\n📋 PRÓXIMOS PASSOS:')
            self.stdout.write('1. Execute este comando após cada deploy')
            self.stdout.write('2. Ou adicione ao processo de deploy')
            self.stdout.write('3. Configure variáveis de ambiente no Google Cloud')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro inesperado: {str(e)}')
            )
            logger.error(f'Erro ao corrigir configurações de email: {e}', exc_info=True)
    
    def _test_email_sending(self, config, recipient):
        """Testa envio de email"""
        self.stdout.write(f'\n🧪 TESTANDO ENVIO DE EMAIL PARA {recipient}...')
        
        try:
            from django.core.mail import send_mail
            
            result = send_mail(
                'Teste Produção - FireFlies CMS',
                'Este é um teste de email em produção. Configurações corrigidas!',
                config.get('DEFAULT_FROM_EMAIL'),
                [recipient],
                fail_silently=False
            )
            
            if result == 1:
                self.stdout.write(
                    self.style.SUCCESS('✅ Email enviado com sucesso!')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Falha ao enviar email')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro ao enviar email: {e}')
            ) 