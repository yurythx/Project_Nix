from django.core.management.base import BaseCommand
from apps.config.models.app_module_config import AppModuleConfiguration


class Command(BaseCommand):
    help = 'Corrige o URL pattern do módulo articles'
    
    def handle(self, *args, **options):
        self.stdout.write('🔧 Corrigindo URL pattern do módulo articles...')
        
        try:
            # Busca o módulo articles
            articles_module = AppModuleConfiguration.objects.filter(app_name='articles').first()
            
            if not articles_module:
                self.stdout.write(
                    self.style.WARNING('⚠️  Módulo articles não encontrado no banco de dados.')
                )
                return
            
            # Mostra configuração atual
            self.stdout.write(f'📋 Configuração atual:')
            self.stdout.write(f'  • App Name: {articles_module.app_name}')
            self.stdout.write(f'  • Display Name: {articles_module.display_name}')
            self.stdout.write(f'  • URL Pattern: {articles_module.url_pattern}')
            self.stdout.write(f'  • Status: {articles_module.status}')
            self.stdout.write(f'  • Enabled: {articles_module.is_enabled}')
            
            # Corrige o URL pattern
            old_pattern = articles_module.url_pattern
            articles_module.url_pattern = 'artigos/'
            articles_module.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ URL pattern atualizado de "{old_pattern}" para "{articles_module.url_pattern}"')
            )
            
            # Verifica se está habilitado
            if not articles_module.is_enabled:
                self.stdout.write(
                    self.style.WARNING('⚠️  Módulo articles está desabilitado. Habilitando...')
                )
                articles_module.is_enabled = True
                articles_module.status = 'active'
                articles_module.save()
                self.stdout.write(
                    self.style.SUCCESS('✅ Módulo articles habilitado com sucesso!')
                )
            
            # Mostra configuração final
            self.stdout.write(f'\n📋 Configuração final:')
            self.stdout.write(f'  • URL Pattern: {articles_module.url_pattern}')
            self.stdout.write(f'  • Status: {articles_module.status}')
            self.stdout.write(f'  • Enabled: {articles_module.is_enabled}')
            
            self.stdout.write(
                self.style.SUCCESS('\n🎉 Correção concluída! Agora /artigos/ deve funcionar corretamente.')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro ao corrigir módulo articles: {str(e)}')
            )
            raise e
