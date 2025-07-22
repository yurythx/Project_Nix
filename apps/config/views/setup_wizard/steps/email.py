from ..base import WizardStepHandler
from django.contrib import messages
from django.shortcuts import redirect, render

class EmailStepHandler(WizardStepHandler):
    def process(self, request, orchestrator):
        config = {
            'email_backend': request.POST.get('email_backend'),
            'email_host': request.POST.get('email_host'),
            'email_port': request.POST.get('email_port'),
            'email_user': request.POST.get('email_user'),
            'email_password': request.POST.get('email_password'),
            'use_tls': request.POST.get('use_tls') == 'on',
            'use_ssl': request.POST.get('use_ssl') == 'on',
            'default_from': request.POST.get('default_from'),
        }
        # Validação simples
        if config['email_backend'] == 'smtp' and (not config['email_host'] or not config['email_user'] or not config['email_password']):
            messages.error(request, "Preencha todos os campos SMTP obrigatórios.")
            return redirect('setup_wizard?step=3')
        orchestrator.save_progress('email', config)
        messages.success(request, "✅ Configurações de e-mail salvas com sucesso.")
        return redirect('setup_wizard?step=4')

    def render_form(self, request):
        # Implemente a lógica para renderizar o formulário de configuração de email
        # Este método deve retornar um objeto de formulário válido
        # Exemplo:
        # form = EmailForm(request.POST)
        # return render(request, self.template_name, {'form': form})
        pass

    def is_valid(self, request):
        # Implemente a lógica para validar os dados do formulário de configuração de email
        # Este método deve retornar True se os dados são válidos, False caso contrário
        # Exemplo:
        # return form.is_valid()
        return True 