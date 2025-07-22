from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.config.services.module_service import ModuleService
from apps.config.models.app_module_config import AppModuleConfiguration

User = get_user_model()


class Command(BaseCommand):
    help = 'Inicializa o sistema de módulos do Havoc'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força a reinicialização mesmo se já existirem módulos',
        )
        parser.add_argument(
            '--sync-only',
            action='store_true',
            help='Apenas sincroniza com apps instalados, não inicializa módulos principais',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Inicializando Sistema de Módulos do Havoc...')
        )
        
        module_service = ModuleService()
        
        # Verifica se já existem módulos
        existing_modules = AppModuleConfiguration.objects.count()
        
        if existing_modules > 0 and not options['force']:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️  Sistema já possui {existing_modules} módulos configurados.'
                )
            )
            self.stdout.write(
                'Use --force para reinicializar ou --sync-only para apenas sincronizar.'
            )
            return
        
        try:
            if not options['sync_only']:
                # Inicializa módulos principais
                self.stdout.write('📦 Inicializando módulos principais...')
                AppModuleConfiguration.initialize_core_modules()
                
                core_modules = AppModuleConfiguration.get_core_modules()
                for module in core_modules:
                    self.stdout.write(
                        f'  ✅ {module.display_name} ({module.app_name})'
                    )
            
            # Sincroniza com apps instalados
            self.stdout.write('🔄 Sincronizando com apps instalados...')
            sync_result = module_service.sync_with_installed_apps()
            
            if sync_result.get('new_modules'):
                self.stdout.write(
                    f'  ✅ Criados {len(sync_result["new_modules"])} novos módulos:'
                )
                for app_name in sync_result['new_modules']:
                    self.stdout.write(f'    - {app_name}')
            else:
                self.stdout.write('  ℹ️  Nenhum novo módulo encontrado.')
            
            if sync_result.get('updated_modules'):
                self.stdout.write(
                    self.style.WARNING(
                        f'  ⚠️  {len(sync_result["updated_modules"])} módulos atualizados para core:'
                    )
                )
                for app_name in sync_result['updated_modules']:
                    self.stdout.write(f'    - {app_name}')
            
            # Após sincronizar, garantir que todos os módulos core estejam habilitados
            core_modules = AppModuleConfiguration.objects.filter(is_core=True)
            updated = 0
            for module in core_modules:
                if not module.is_enabled:
                    module.is_enabled = True
                    module.save()
                    updated += 1
            if updated:
                self.stdout.write(self.style.SUCCESS(f'🔓 {updated} módulos core foram habilitados automaticamente.'))
            
            # Estatísticas finais
            stats = module_service.get_module_statistics()
            self.stdout.write('\n📊 Estatísticas do Sistema:')
            self.stdout.write(f'  • Total de módulos: {stats["total"]}')
            self.stdout.write(f'  • Módulos habilitados: {stats["enabled"]}')
            self.stdout.write(f'  • Módulos principais: {stats["core"]}')
            self.stdout.write(f'  • Módulos personalizados: {stats["custom"]}')
            
            # Lista módulos habilitados
            enabled_modules = module_service.get_enabled_modules()
            self.stdout.write('\n🟢 Módulos Habilitados:')
            for module in enabled_modules:
                status_icon = '🔒' if module.is_core else '📦'
                self.stdout.write(
                    f'  {status_icon} {module.display_name} ({module.app_name})'
                )
            
            self.stdout.write(
                self.style.SUCCESS('\n✅ Sistema de módulos inicializado com sucesso!')
            )
            self.stdout.write(
                'Acesse /config/modulos/ para gerenciar os módulos do sistema.'
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro ao inicializar sistema de módulos: {str(e)}')
            )
            raise e
