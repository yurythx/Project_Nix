from django.core.management.base import BaseCommand
from django.conf import settings
from django.urls import reverse, NoReverseMatch
from apps.config.models.app_module_config import AppModuleConfiguration
from apps.config.services.module_service import ModuleService


class Command(BaseCommand):
    help = 'Verifica e corrige inconsistências de URLs dos módulos'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Corrige automaticamente as inconsistências encontradas',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔍 Verificando URLs dos módulos...')
        )
        
        module_service = ModuleService()
        all_modules = module_service.get_all_modules()
        
        # URLs reais do Django (core/urls.py)
        real_urls = {
            'accounts': 'accounts/',
            'config': 'config/',
            'articles': 'artigos/',  # URL real é /artigos/
            'pages': '',  # URL raiz
        }
        
        inconsistencies = []
        
        for module in all_modules:
            self.stdout.write(f'\n📋 Verificando módulo: {module.display_name} ({module.app_name})')
            
            # Verifica se o URL pattern está correto
            expected_url = real_urls.get(module.app_name)
            current_url = module.url_pattern
            
            if expected_url is not None:
                if current_url != expected_url:
                    inconsistency = {
                        'module': module,
                        'current': current_url,
                        'expected': expected_url,
                        'type': 'url_mismatch'
                    }
                    inconsistencies.append(inconsistency)
                    
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⚠️  URL inconsistente: "{current_url}" → deveria ser "{expected_url}"'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✅ URL correto: "{current_url}"')
                    )
            else:
                self.stdout.write(
                    self.style.WARNING(f'  ❓ URL não mapeado: "{current_url}"')
                )
            
            # Verifica se o módulo está habilitado
            if not module.is_available:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠️  Módulo desabilitado: {module.status}')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'  ✅ Módulo habilitado')
                )
            
            # Testa acesso à URL (se habilitado)
            if module.is_available and module.url_pattern:
                try:
                    # Simula teste de acesso
                    test_url = f'/{module.url_pattern}'
                    self.stdout.write(f'  🔗 URL de teste: {test_url}')
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'  ❌ Erro ao testar URL: {str(e)}')
                    )
        
        # Resumo das inconsistências
        if inconsistencies:
            self.stdout.write(
                self.style.WARNING(f'\n⚠️  Encontradas {len(inconsistencies)} inconsistências:')
            )
            
            for inc in inconsistencies:
                self.stdout.write(
                    f'  • {inc["module"].display_name}: "{inc["current"]}" → "{inc["expected"]}"'
                )
            
            # Corrige automaticamente se solicitado
            if options['fix']:
                self.stdout.write('\n🔧 Corrigindo inconsistências...')
                
                for inc in inconsistencies:
                    module = inc['module']
                    old_url = inc['current']
                    new_url = inc['expected']
                    
                    module.url_pattern = new_url
                    module.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✅ {module.display_name}: "{old_url}" → "{new_url}"'
                        )
                    )
                
                self.stdout.write(
                    self.style.SUCCESS('\n🎉 Todas as inconsistências foram corrigidas!')
                )
            else:
                self.stdout.write(
                    '\n💡 Use --fix para corrigir automaticamente as inconsistências.'
                )
        else:
            self.stdout.write(
                self.style.SUCCESS('\n✅ Nenhuma inconsistência encontrada!')
            )
        
        # Estatísticas finais
        stats = module_service.get_module_statistics()
        self.stdout.write(f'\n📊 Estatísticas dos Módulos:')
        self.stdout.write(f'  • Total: {stats["total"]}')
        self.stdout.write(f'  • Habilitados: {stats["enabled"]}')
        self.stdout.write(f'  • Principais: {stats["core"]}')
        self.stdout.write(f'  • Personalizados: {stats["custom"]}')
        
        # URLs de teste
        self.stdout.write(f'\n🔗 URLs para Testar:')
        for module in all_modules:
            if module.is_available and module.url_pattern:
                test_url = f'http://localhost:8000/{module.url_pattern}'
                self.stdout.write(f'  • {module.display_name}: {test_url}')
        
        self.stdout.write(
            self.style.SUCCESS('\n✅ Verificação concluída!')
        )
