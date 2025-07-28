from django.core.management.base import BaseCommand
from apps.config.models.app_module_config import AppModuleConfiguration
from apps.config.services.module_service import ModuleService


class Command(BaseCommand):
    help = 'Ativa o módulo articles e outros módulos principais'

    def handle(self, *args, **options):
        self.stdout.write('Ativando módulos principais...')
        
        # Lista de módulos que devem estar ativos
        modules_to_activate = ['articles', 'books', 'audiobooks', 'mangas']
        
        for module_name in modules_to_activate:
            try:
                # Busca o módulo
                module = AppModuleConfiguration.objects.filter(app_name=module_name).first()
                
                if module:
                    # Ativa o módulo
                    module.is_enabled = True
                    module.status = 'active'
                    module.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Módulo {module_name} ativado com sucesso')
                    )
                else:
                    # Cria o módulo se não existir
                    module_data = {
                        'app_name': module_name,
                        'display_name': module_name.title(),
                        'description': f'Módulo {module_name}',
                        'is_enabled': True,
                        'is_core': False,
                        'status': 'active',
                        'module_type': 'feature',
                        'menu_icon': 'fas fa-puzzle-piece',
                        'menu_order': 30,
                    }
                    
                    new_module = AppModuleConfiguration.objects.create(**module_data)
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Módulo {module_name} criado e ativado')
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Erro ao ativar módulo {module_name}: {str(e)}')
                )
        
        # Sincroniza com apps instalados
        try:
            module_service = ModuleService()
            sync_result = module_service.sync_with_installed_apps()
            
            if sync_result['success']:
                self.stdout.write(
                    self.style.SUCCESS('✅ Sincronização com apps instalados concluída')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️ Sincronização com avisos: {sync_result.get("error", "")}')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro na sincronização: {str(e)}')
            )
        
        self.stdout.write(
            self.style.SUCCESS('🎉 Ativação de módulos concluída!')
        ) 