from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import DetailView, UpdateView, ListView, DeleteView
from django.views import View
from django.http import JsonResponse
from apps.config.models.app_module_config import AppModuleConfiguration
from apps.config.services.module_service import ModuleService
from apps.config.forms.module_forms import ModuleConfigurationForm


class ModuleListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    Lista todos os módulos do sistema.
    Exibe módulos habilitados, desabilitados e estatísticas.
    """
    model = AppModuleConfiguration
    template_name = 'config/modules/list.html'
    context_object_name = 'modules'

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        module_service = ModuleService()
        all_modules = module_service.get_all_modules()
        installed_apps = module_service.get_installed_apps_list()
        # Padroniza nomes para comparar sem prefixo 'apps.'
        installed_names = set([a.split('.')[-1] for a in installed_apps])
        filtered = [m for m in all_modules if m.app_name.split('.')[-1] in installed_names]
        return filtered

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        module_service = ModuleService()
        page_modules = context.get('page_obj') or context.get('modules') or []
        print("[DEBUG] page_modules:", page_modules)  # Depuração temporária
        enabled_modules = module_service.get_enabled_modules()
        disabled_modules = [m for m in page_modules if not m.is_available]
        module_tests = [
            {
                'module': module,
                'test_result': self._simple_module_access_test(module)
            }
            for module in page_modules
        ]
        module_stats = module_service.get_module_statistics()
        def module_row(module):
            return [
                module.display_name,
                module.app_name,
                module.get_module_type_display() if hasattr(module, 'get_module_type_display') else getattr(module, 'type', ''),
                'Ativo' if module.is_enabled else 'Inativo',
                'Disponível' if module.is_available else 'Indisponível',
                module.menu_order,
            ]
        def config_row(module):
            return [
                module.display_name,
                module.app_name,
                'Ativo' if module.is_enabled else 'Inativo',
                module.menu_order,
            ]
        rows = [module_row(m) for m in page_modules]
        config_rows = [config_row(m) for m in page_modules]
        context.update({
            'enabled_modules': enabled_modules,
            'disabled_modules': disabled_modules,
            'module_tests': module_tests,
            'module_stats': module_stats,
            'rows': rows,
            'config_rows': config_rows,
            'page_title': 'Gerenciamento de Módulos',
            'page_description': 'Configure e teste os módulos do sistema',
        })
        return context

    def _simple_module_access_test(self, module):
        """Testa se um módulo está acessível de forma simplificada"""
        if not module.is_available:
            return {
                'accessible': False,
                'reason': 'Módulo desabilitado ou inativo',
                'status': 'disabled'
            }
        # Verifica dependências
        if module.dependencies:
            for dep_name in module.dependencies:
                dep = AppModuleConfiguration.objects.filter(app_name=dep_name).first()
                if not dep or not dep.is_available:
                    return {
                        'accessible': False,
                        'reason': f'Dependência {dep_name} não disponível',
                        'status': 'dependency_error'
                    }
        if not module.url_pattern:
            return {
                'accessible': True,
                'reason': 'Módulo sem URL específica',
                'status': 'no_url'
            }
        return {
            'accessible': True,
            'reason': 'Módulo totalmente funcional',
            'status': 'ok'
        }


class ModuleDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Detalhes de um módulo específico"""
    model = AppModuleConfiguration
    template_name = 'config/modules/detail.html'
    context_object_name = 'module'
    slug_field = 'app_name'
    slug_url_kwarg = 'app_name'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        module_service = ModuleService()
        
        # Valida dependências
        dependencies_info = module_service.validate_module_dependencies(
            self.object.app_name
        )
        
        # Busca módulos dependentes
        dependent_modules = self.object.get_dependent_modules()
        
        context.update({
            'dependencies_info': dependencies_info,
            'dependent_modules': dependent_modules,
            'page_title': f'Módulo: {self.object.display_name}',
        })
        return context


class ModuleUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Edita configurações de um módulo"""
    model = AppModuleConfiguration
    form_class = ModuleConfigurationForm
    template_name = 'config/modules/update.html'
    slug_field = 'app_name'
    slug_url_kwarg = 'app_name'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(
            self.request,
            f'Módulo "{form.instance.display_name}" atualizado com sucesso!'
        )
        return super().form_valid(form)
    
    def get_success_url(self):
        from django.urls import reverse
        return reverse('config:module_detail', kwargs={'app_name': self.object.app_name})


class ModuleStatsAPIView(LoginRequiredMixin, UserPassesTestMixin, View):
    """API para estatísticas dos módulos"""
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get(self, request):
        module_service = ModuleService()
        stats = module_service.get_module_statistics()
        
        # Adiciona informações detalhadas
        modules_by_type = {}
        for module in AppModuleConfiguration.objects.all():
            module_type = module.get_module_type_display()
            if module_type not in modules_by_type:
                modules_by_type[module_type] = {'total': 0, 'enabled': 0}
            
            modules_by_type[module_type]['total'] += 1
            if module.is_enabled:
                modules_by_type[module_type]['enabled'] += 1
        
        stats['by_type'] = modules_by_type
        
        return JsonResponse(stats)


class ModuleDependencyCheckView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Verifica dependências de um módulo"""

    def test_func(self):
        return self.request.user.is_staff

    def get(self, request, app_name):
        module_service = ModuleService()
        dependencies_info = module_service.validate_module_dependencies(app_name)

        return JsonResponse(dependencies_info)


class ModuleEnableView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Habilita um módulo"""
    def test_func(self):
        return self.request.user.is_staff

    def post(self, request, app_name):
        module_service = ModuleService()
        module = get_object_or_404(AppModuleConfiguration, app_name=app_name)
        try:
            success = module_service.enable_module(app_name, request.user)
            if success:
                messages.success(request, f'Módulo "{module.display_name}" habilitado com sucesso!')
            else:
                # Buscar motivo detalhado
                module = module_service.get_module_by_name(app_name)
                dep_info = module_service.validate_module_dependencies(app_name)
                if dep_info.get('missing_dependencies') or dep_info.get('inactive_dependencies'):
                    msg = f"Dependências não atendidas: "
                    if dep_info.get('missing_dependencies'):
                        msg += f"Ausentes: {', '.join(dep_info['missing_dependencies'])}. "
                    if dep_info.get('inactive_dependencies'):
                        msg += f"Inativas: {', '.join(dep_info['inactive_dependencies'])}. "
                    messages.error(request, f'Erro ao habilitar o módulo "{module.display_name}": {msg}')
                else:
                    messages.error(request, f'Erro ao habilitar o módulo "{module.display_name}". Verifique os logs para mais detalhes.')
        except Exception as e:
            messages.error(request, f'Erro inesperado ao habilitar o módulo: {str(e)}')
        return redirect('config:module_list')


class ModuleDisableView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Desabilita um módulo"""
    def test_func(self):
        return self.request.user.is_staff

    def post(self, request, app_name):
        module_service = ModuleService()
        module = get_object_or_404(AppModuleConfiguration, app_name=app_name)
        if module.is_core:
            messages.error(request, f'🔒 O módulo "{module.display_name}" é essencial e não pode ser desativado.')
            return redirect('config:module_list')
        try:
            success = module_service.disable_module(app_name, request.user)
            if success:
                messages.success(request, f'Módulo "{module.display_name}" desabilitado com sucesso!')
            else:
                dependentes = module.get_dependent_modules()
                if dependentes.exists():
                    dep_names = ', '.join([m.display_name for m in dependentes])
                    messages.error(request, f'Erro ao desabilitar o módulo "{module.display_name}": outros módulos dependem dele: {dep_names}.')
                else:
                    messages.error(request, f'Erro ao desabilitar o módulo "{module.display_name}". Verifique os logs para mais detalhes.')
        except Exception as e:
            messages.error(request, f'Erro inesperado ao desabilitar o módulo: {str(e)}')
        return redirect('config:module_list')


class ModuleTestView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Testa acessibilidade de um módulo"""
    def test_func(self):
        return self.request.user.is_staff

    def post(self, request, app_name):
        module = get_object_or_404(AppModuleConfiguration, app_name=app_name)
        result = self._simple_module_access_test(module)
        if result['accessible']:
            messages.success(request, f'Módulo "{module.display_name}" está acessível.')
        else:
            messages.warning(request, f'Módulo "{module.display_name}" não está acessível: {result["reason"]}')
        return redirect('config:module_list')

    def _simple_module_access_test(self, module):
        if not module.is_available:
            return {
                'accessible': False,
                'reason': 'Módulo desabilitado ou inativo',
                'status': 'disabled'
            }
        if module.dependencies:
            for dep_name in module.dependencies:
                dep = AppModuleConfiguration.objects.filter(app_name=dep_name).first()
                if not dep or not dep.is_available:
                    return {
                        'accessible': False,
                        'reason': f'Dependência {dep_name} não disponível',
                        'status': 'dependency_error'
                    }
        if not module.url_pattern:
            return {
                'accessible': True,
                'reason': 'Módulo sem URL específica',
                'status': 'no_url'
            }
        return {
            'accessible': True,
            'reason': 'Módulo totalmente funcional',
            'status': 'ok'
        }


class ModuleDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = AppModuleConfiguration
    template_name = 'config/modules/delete.html'
    slug_field = 'app_name'
    slug_url_kwarg = 'app_name'
    success_url = '/config/modules/'

    def test_func(self):
        return self.request.user.is_staff

    def delete(self, request, *args, **kwargs):
        module = self.get_object()
        if module.is_core:
            messages.error(request, f'🔒 O módulo "{module.display_name}" é essencial e não pode ser deletado.')
            return redirect('config:module_list')
        messages.success(request, f'Módulo "{module.display_name}" deletado com sucesso!')
        return super().delete(request, *args, **kwargs)
