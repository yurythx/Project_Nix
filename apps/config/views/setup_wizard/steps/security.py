from ..base import WizardStepHandler
from django.contrib import messages
from django.shortcuts import redirect

class SecurityStepHandler(WizardStepHandler):
    def process(self, request, orchestrator):
        config = {
            'security_mode': request.POST.get('security_mode'),
            'allowed_hosts': request.POST.get('allowed_hosts'),
            'csrf_trusted_origins': request.POST.get('csrf_trusted_origins'),
            'security_level': request.POST.get('security_level'),
            'session_timeout': request.POST.get('session_timeout'),
            'enable_https': request.POST.get('enable_https') == 'on',
        }
        orchestrator.save_progress('security', config)
        messages.success(request, "✅ Configurações de segurança salvas.")
        return redirect('setup_wizard?step=5')

    def form_valid(self, form):
        # Lógica para salvar os dados na sessão ou no banco de dados temporário
        # Exemplo: request.session['security_config'] = form.cleaned_data
        messages.success(self.request, "✅ Configurações de segurança salvas.")
        return super().form_valid(form) 