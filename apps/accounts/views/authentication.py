from django.views.generic.edit import FormView
from django.views.generic.base import RedirectView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from apps.accounts.forms.authentication import FlexibleLoginForm

@method_decorator([csrf_protect, never_cache], name='dispatch')
class LoginView(FormView):
    """View para login de usuários com suporte a email e username"""
    template_name = 'accounts/login.html'
    form_class = FlexibleLoginForm
    success_url = reverse_lazy('pages:home')

    def get(self, request):
        """Exibe o formulário de login"""
        if request.user.is_authenticated:
            messages.info(request, '✅ Você já está logado.')
            return redirect('pages:home')

        # Verificar se há contexto de tentativa de acesso
        login_context = request.session.get('login_context', {})
        if login_context:
            attempted_area = login_context.get('attempted_area', 'esta área')
            messages.info(
                request,
                f'🔐 Para acessar {attempted_area}, faça login com seu e-mail ou nome de usuário.'
            )
            # Limpar contexto após usar
            del request.session['login_context']

        form = self.form_class(request=request)
        return render(request, self.template_name, {'form': form})

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        remember_me = form.cleaned_data.get('remember_me', False)
        if remember_me:
            self.request.session.set_expiry(1209600)
        else:
            self.request.session.set_expiry(0)
        greeting = self.get_greeting()
        name = user.get_full_name() or user.first_name or user.username
        messages.success(
            self.request,
            f'🎉 {greeting}, {name}! Login realizado com sucesso.'
        )
        next_url = self.request.GET.get('next')
        if next_url:
            self.success_url = next_url
        return super().form_valid(form)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get_greeting(self):
        """Retorna saudação baseada no horário"""
        from datetime import datetime
        hour = datetime.now().hour

        if 5 <= hour < 12:
            return "Bom dia"
        elif 12 <= hour < 18:
            return "Boa tarde"
        else:
            return "Boa noite"

class LogoutView(AccessMixin, RedirectView):
    """View para logout de usuários"""
    url = reverse_lazy('pages:home')

    def get(self, request, *args, **kwargs):
        """Processa o logout"""
        if request.user.is_authenticated:
            logout(request)
            messages.success(request, 'Você foi desconectado com sucesso.')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Processa o logout via POST"""
        return self.get(request, *args, **kwargs)