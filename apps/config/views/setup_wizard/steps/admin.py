from ..base import WizardStepHandler
from django.contrib import messages
from django.shortcuts import redirect

class AdminStepHandler(WizardStepHandler):
    def process(self, request, orchestrator):
        config = {
            'username': request.POST.get('username'),
            'email': request.POST.get('email'),
            'password': request.POST.get('password'),
            'password_confirm': request.POST.get('password_confirm'),
            'first_name': request.POST.get('first_name'),
            'last_name': request.POST.get('last_name'),
        }
        # Validação simples
        if not config['username'] or not config['email'] or not config['password']:
            messages.error(request, "Preencha todos os campos obrigatórios.")
            return redirect('setup_wizard?step=2')
        if config['password'] != config['password_confirm']:
            messages.error(request, "As senhas não coincidem.")
            return redirect('setup_wizard?step=2')
        orchestrator.save_progress('admin', config)
        messages.success(request, "Configuração do administrador salva!")
        return redirect('setup_wizard?step=3')

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            self.wizard.set_step_data('admin', form.cleaned_data)
            self.wizard.save()
            messages.success(request, "✅ Conta de administrador criada com sucesso!")
            return redirect('setup_wizard?step=2')
        else:
            if 'password_confirm' in form.errors:
                messages.error(request, "🔑 As senhas não conferem. Tente novamente.")
            else:
                messages.error(request, "📝 Por favor, preencha todos os campos obrigatórios.")
            return self.render_to_response(self.get_context_data(form=form))

    def form_valid(self, form):
        # Lógica para salvar os dados na sessão ou no banco de dados temporário
        # Exemplo: request.session['admin_config'] = form.cleaned_data
        messages.success(self.request, "Configuração do administrador salva!")
        return super().form_valid(form)

    def form_invalid(self, form):
        if form.has_error('password', code='password_mismatch'):
            messages.error(self.request, "As senhas não coincidem.")
        else:
            messages.error(self.request, "Preencha todos os campos obrigatórios.")
        return super().form_invalid(form) 