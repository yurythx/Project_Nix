from typing import List, Dict, Optional
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.conf import settings
from apps.config.models.app_module_config import AppModuleConfiguration
from apps.config.interfaces.services import IModuleService
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class ModuleService(IModuleService):
    """
    Serviço para gerenciamento de módulos do sistema.
    Permite criar, atualizar, habilitar, desabilitar e consultar módulos, além de validar dependências.
    """
    
    def __init__(self):
        self.core_apps = AppModuleConfiguration.CORE_APPS
    
    def get_all_modules(self) -> List[AppModuleConfiguration]:
        """Retorna todos os módulos"""
        return AppModuleConfiguration.objects.all().order_by('menu_order', 'display_name')

    def get_enabled_modules(self) -> List[AppModuleConfiguration]:
        """Retorna todos os módulos habilitados"""
        return AppModuleConfiguration.get_enabled_modules()
    
    def get_available_modules(self) -> List[AppModuleConfiguration]:
        """Retorna módulos disponíveis para uso"""
        return AppModuleConfiguration.objects.filter(
            is_enabled=True,
            status='active'
        ).order_by('menu_order', 'display_name')
    
    def get_menu_modules(self) -> List[AppModuleConfiguration]:
        """Retorna módulos que devem aparecer no menu"""
        return self.get_available_modules().filter(show_in_menu=True)
    
    def get_module_by_name(self, app_name: str) -> Optional[AppModuleConfiguration]:
        """Busca módulo por nome, tolerante a prefixo 'apps.'"""
        try:
            return AppModuleConfiguration.objects.get(app_name=app_name)
        except AppModuleConfiguration.DoesNotExist:
            # Tenta sem o prefixo 'apps.' se houver
            if app_name.startswith('apps.'):
                alt_name = app_name.split('.', 1)[1]
            else:
                alt_name = f'apps.{app_name}'
            try:
                return AppModuleConfiguration.objects.get(app_name=alt_name)
            except AppModuleConfiguration.DoesNotExist:
                return None
    
    def is_module_enabled(self, app_name: str) -> bool:
        """Verifica se um módulo está habilitado"""
        module = self.get_module_by_name(app_name)
        print(f"[DEBUG is_module_enabled] app_name={app_name} module={module} is_enabled={getattr(module, 'is_enabled', None)} status={getattr(module, 'status', None)}")
        return module.is_available if module else False
    
    def is_core_module(self, app_name: str) -> bool:
        """Verifica se é um módulo principal"""
        return app_name in self.core_apps
    
    @transaction.atomic
    def enable_module(self, app_name: str, user=None) -> bool:
        """Habilita um módulo"""
        try:
            module = self.get_module_by_name(app_name)
            if not module:
                logger.error(f"Módulo {app_name} não encontrado")
                return False
            
            # Verifica dependências
            if not module.check_dependencies():
                logger.error(f"Dependências do módulo {app_name} não atendidas")
                return False
            
            module.is_enabled = True
            module.status = 'active'
            module.updated_by = user
            module.save()
            
            logger.info(f"Módulo {app_name} habilitado por {user.email if user else 'sistema'}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao habilitar módulo {app_name}: {str(e)}")
            return False
    
    @transaction.atomic
    def disable_module(self, app_name: str, user=None) -> bool:
        """Desabilita um módulo (se não for principal)"""
        try:
            module = self.get_module_by_name(app_name)
            if not module:
                logger.error(f"Módulo {app_name} não encontrado")
                return False
            
            # Não permite desabilitar módulos principais
            if module.is_core:
                logger.error(f"Tentativa de desabilitar módulo principal: {app_name}")
                return False
            
            # Verifica se outros módulos dependem deste
            dependent_modules = module.get_dependent_modules()
            if dependent_modules.exists():
                dependent_names = [m.display_name for m in dependent_modules]
                logger.error(f"Módulo {app_name} não pode ser desabilitado. Dependências: {dependent_names}")
                return False
            
            module.is_enabled = False
            module.status = 'inactive'
            module.updated_by = user
            module.save()
            
            logger.info(f"Módulo {app_name} desabilitado por {user.email if user else 'sistema'}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao desabilitar módulo {app_name}: {str(e)}")
            return False
    
    @transaction.atomic
    def create_module(self, module_data: Dict, user: User = None) -> Optional[AppModuleConfiguration]:
        """Cria um novo módulo"""
        try:
            # Verifica se já existe
            if self.get_module_by_name(module_data.get('app_name')):
                logger.info(f"Módulo {module_data.get('app_name')} já existe, ignorando criação.")
                return None
            
            module = AppModuleConfiguration(
                created_by=user,
                updated_by=user,
                **module_data
            )
            module.full_clean()
            module.save()
            
            logger.info(f"Módulo {module.app_name} criado por {user.email if user else 'sistema'}")
            return module
            
        except ValidationError as e:
            logger.error(f"Erro de validação ao criar módulo: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Erro ao criar módulo: {str(e)}")
            return None
    
    @transaction.atomic
    def update_module(self, app_name: str, module_data: Dict, user: User = None) -> bool:
        """Atualiza um módulo existente"""
        try:
            module = self.get_module_by_name(app_name)
            if not module:
                logger.error(f"Módulo {app_name} não encontrado")
                return False
            # Centralizar regra crítica aqui:
            if module.is_core and module_data.get('status') != 'active':
                raise ValueError('Módulos principais devem permanecer ativos.')
            # Atualiza campos permitidos
            allowed_fields = [
                'display_name', 'description', 'url_pattern', 'menu_icon',
                'menu_order', 'show_in_menu', 'dependencies', 'required_permissions',
                'module_settings', 'version', 'author', 'documentation_url',
                'is_enabled', 'status'
            ]
            for field, value in module_data.items():
                if field in allowed_fields:
                    setattr(module, field, value)
            module.updated_by = user
            module.full_clean()
            module.save()
            logger.info(f"Módulo {app_name} atualizado por {user.email if user else 'sistema'}")
            return True
        except ValidationError as e:
            logger.error(f"Erro de validação ao atualizar módulo {app_name}: {str(e)}")
            return False
        except ValueError as e:
            logger.error(f"Regra de negócio violada ao atualizar módulo {app_name}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Erro ao atualizar módulo {app_name}: {str(e)}")
            return False
    
    def get_module_statistics(self) -> Dict:
        """Retorna estatísticas dos módulos"""
        total = AppModuleConfiguration.objects.count()
        enabled = AppModuleConfiguration.objects.filter(is_enabled=True).count()
        core = AppModuleConfiguration.objects.filter(is_core=True).count()
        
        return {
            'total': total,
            'enabled': enabled,
            'disabled': total - enabled,
            'core': core,
            'custom': total - core,
        }
    
    def validate_module_dependencies(self, app_name: str) -> Dict:
        """Valida as dependências de um módulo"""
        module = self.get_module_by_name(app_name)
        if not module:
            return {'valid': False, 'error': 'Módulo não encontrado'}
        
        if not module.dependencies:
            return {'valid': True, 'dependencies': []}
        
        missing_deps = []
        inactive_deps = []
        
        for dep_name in module.dependencies:
            dep_module = self.get_module_by_name(dep_name)
            if not dep_module:
                missing_deps.append(dep_name)
            elif not dep_module.is_enabled:
                inactive_deps.append(dep_name)
        
        return {
            'valid': len(missing_deps) == 0 and len(inactive_deps) == 0,
            'missing_dependencies': missing_deps,
            'inactive_dependencies': inactive_deps,
            'all_dependencies': module.dependencies
        }
    
    def get_installed_apps_list(self) -> List[str]:
        """Retorna lista de apps locais definidos explicitamente em settings.LOCAL_APPS"""
        return getattr(settings, 'LOCAL_APPS', [])
    
    def sync_with_installed_apps(self, user: User = None) -> Dict:
        """Sincroniza módulos com apps instalados, padronizando nomes SEM o prefixo 'apps.'"""
        try:
            installed_apps = self.get_installed_apps_list()
            # Extrai nomes sem o prefixo 'apps.'
            installed_app_names = [app.split('.')[-1] for app in installed_apps]
            existing_modules = {m.app_name for m in self.get_all_modules()}

            new_modules = []
            updated_modules = []

            for app_path in installed_apps:
                app_name = app_path.split('.')[-1]  # sempre sem prefixo
                if app_name not in existing_modules:
                    # Cria novo módulo
                    module_data = {
                        'app_name': app_name,
                        'display_name': app_name.title(),
                        'description': f'Módulo {app_name}',
                        'is_enabled': app_name in self.core_apps,
                        'is_core': app_name in self.core_apps,
                        'status': 'active' if app_name in self.core_apps else 'inactive'
                    }
                    new_module = self.create_module(module_data, user)
                    if new_module:
                        new_modules.append(new_module.app_name)
                else:
                    # Atualiza módulo existente se necessário
                    module = self.get_module_by_name(app_name)
                    if module and not module.is_core and app_name in self.core_apps:
                        module.is_core = True
                        module.is_enabled = True
                        module.status = 'active'
                        module.save()
                        updated_modules.append(app_name)

            return {
                'success': True,
                'new_modules': new_modules,
                'updated_modules': updated_modules,
                'total_installed': len(installed_apps),
                'total_modules': len(self.get_all_modules())
            }

        except Exception as e:
            logger.error(f"Erro ao sincronizar módulos: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def initialize_system(self, user: User = None):
        """Inicializa o sistema com módulos padrão"""
        try:
            # Sincroniza com apps instalados
            sync_result = self.sync_with_installed_apps(user)
            
            if not sync_result['success']:
                logger.error(f"Erro na sincronização: {sync_result['error']}")
                return False
            
            logger.info("Sistema inicializado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao inicializar sistema: {str(e)}")
            return False
