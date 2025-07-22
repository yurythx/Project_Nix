from django.http import Http404
from apps.config.services.module_service import ModuleService

class SuccessMessageMixin:
    """Adiciona mensagem de sucesso ao contexto da view"""
    success_message = None
    def form_valid(self, form):
        response = super().form_valid(form)
        if self.success_message:
            from django.contrib import messages
            messages.success(self.request, self.success_message)
        return response 

class ModuleEnabledRequiredMixin:
    module_name = None  # Ex: 'apps.articles'

    def dispatch(self, request, *args, **kwargs):
        service = ModuleService()
        if not self.module_name:
            raise ValueError('Defina module_name no Mixin')
        if not service.is_module_enabled(self.module_name):
            raise Http404('Módulo inativo')
        return super().dispatch(request, *args, **kwargs) 