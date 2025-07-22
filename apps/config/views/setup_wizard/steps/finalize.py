from ..base import WizardStepHandler
from django.contrib import messages
from django.shortcuts import redirect
from apps.config.models.app_module_config import AppModuleConfiguration
from apps.config.services.module_service import ModuleService
import logging

logger = logging.getLogger(__name__)

class FinalizeStepHandler(WizardStepHandler):
    def process(self, request, orchestrator):
        # Aplica todas as configurações salvas
        success = orchestrator.apply_all_configurations()
        if success:
            try:
                # Inicializa módulos core e sincroniza módulos instalados
                logger.info("Inicializando módulos core...")
                self._initialize_core_modules()
                
                logger.info("Sincronizando módulos instalados...")
                module_service = ModuleService()
                sync_result = module_service.sync_with_installed_apps()
                
                if sync_result.get('success'):
                    logger.info(f"Módulos sincronizados: {sync_result.get('new_modules', [])}")
                else:
                    logger.error(f"Erro na sincronização: {sync_result.get('error', 'Erro desconhecido')}")
                
                messages.success(request, "🎉 Tudo pronto! Sua configuração foi finalizada com sucesso.")
                return redirect('config:dashboard')
            except Exception as e:
                logger.error(f"Erro ao finalizar a configuração: {e}", exc_info=True)
                messages.warning(request, f"⚠️ Configuração concluída, mas alguns módulos não puderam ser inicializados: {str(e)}")
                return redirect('config:dashboard')
        else:
            messages.error(request, "Erro ao finalizar configuração.")
            return redirect('setup_wizard?step=5')
    
    def _initialize_core_modules(self):
        """Inicializa os módulos principais de forma mais robusta"""
        try:
            core_modules_data = [
                {
                    'app_name': 'accounts',
                    'display_name': 'Contas e Usuários',
                    'description': 'Sistema de autenticação, registro e gerenciamento de usuários',
                    'url_pattern': 'accounts/',
                    'menu_icon': 'fas fa-users',
                    'menu_order': 10,
                    'module_type': 'core',
                    'is_core': True,
                    'is_enabled': True,
                    'status': 'active',
                },
                {
                    'app_name': 'config',
                    'display_name': 'Configurações',
                    'description': 'Painel de configurações e administração do sistema',
                    'url_pattern': 'config/',
                    'menu_icon': 'fas fa-cogs',
                    'menu_order': 90,
                    'module_type': 'core',
                    'is_core': True,
                    'is_enabled': True,
                    'status': 'active',
                },
                {
                    'app_name': 'pages',
                    'display_name': 'Páginas',
                    'description': 'Sistema de páginas estáticas e dinâmicas',
                    'url_pattern': '',
                    'menu_icon': 'fas fa-file-alt',
                    'menu_order': 20,
                    'module_type': 'core',
                    'is_core': True,
                    'is_enabled': True,
                    'status': 'active',
                },
            ]
            
            for module_data in core_modules_data:
                module, created = AppModuleConfiguration.objects.get_or_create(
                    app_name=module_data['app_name'],
                    defaults=module_data
                )
                updated = False
                # Atualiza campos principais se necessário
                for field in ['display_name', 'description', 'url_pattern', 'menu_icon', 'menu_order', 'module_type']:
                    if getattr(module, field) != module_data[field]:
                        setattr(module, field, module_data[field])
                        updated = True
                # Garante que está habilitado, ativo e core
                if not module.is_enabled or module.status != 'active' or not module.is_core:
                    module.is_enabled = True
                    module.status = 'active'
                    module.is_core = True
                    updated = True
                if updated:
                    module.save()
                if created:
                    logger.info(f"Módulo core criado: {module.app_name}")
                else:
                    logger.info(f"Módulo core já existia (atualizado se necessário): {module.app_name}")
        except Exception as e:
            logger.error(f"Erro ao inicializar módulos core: {str(e)}", exc_info=True)
            raise e 