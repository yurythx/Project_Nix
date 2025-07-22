from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model
from django import forms
from apps.accounts.services.password_service import PasswordService
from apps.accounts.repositories.user_repository import DjangoUserRepository
from apps.accounts.repositories.verification_repository import DjangoVerificationRepository
from apps.accounts.notifications.email_notification import EmailNotificationService

User = get_user_model()

class PasswordResetForm(forms.Form):
    """Formulário para solicitar redefinição de senha"""
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite seu e-mail',
            'autocomplete': 'email',
            'autofocus': True
        }),
        help_text='Digite o e-mail associado à sua conta'
    )

class PasswordResetRequestView(View):
    """View para solicitar redefinição de senha"""
    template_name = 'accounts/password_reset/request.html'

    def get(self, request):
        """Exibe o formulário de solicitação"""
        form = PasswordResetForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        """Processa a solicitação de redefinição"""
        form = PasswordResetForm(request.POST)
        
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})
        
        email = form.cleaned_data['email']

        service = PasswordService(
            user_repository=DjangoUserRepository(),
            verification_repository=DjangoVerificationRepository(),
            notification_service=EmailNotificationService()
        )

        try:
            if service.request_password_reset(email):
                messages.success(
                    request,
                    'Se o email estiver cadastrado, você receberá um código para redefinir sua senha.'
                )
                # Redireciona para página de confirmação
                request.session['reset_email'] = email
                return redirect('accounts:password_reset_confirm')
        except Exception as e:
            messages.error(request, 'Ocorreu um erro. Tente novamente.')

        return render(request, self.template_name)

class PasswordResetConfirmView(View):
    """View para confirmar redefinição de senha"""
    template_name = 'accounts/password_reset/confirm.html'

    def get(self, request):
        """Exibe o formulário de confirmação"""
        if 'reset_email' not in request.session:
            messages.warning(request, 'Solicite a redefinição de senha primeiro.')
            return redirect('accounts:password_reset')

        email = request.session['reset_email']
        return render(request, self.template_name, {'email': email})

    def post(self, request):
        """Processa a confirmação da redefinição"""
        email = request.POST.get('email')
        code = request.POST.get('code')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not all([email, code, new_password, confirm_password]):
            messages.error(request, 'Todos os campos são obrigatórios.')
            return render(request, self.template_name, {'email': email})

        if new_password != confirm_password:
            messages.error(request, 'As senhas não coincidem.')
            return render(request, self.template_name, {'email': email})

        service = PasswordService(
            user_repository=DjangoUserRepository(),
            verification_repository=DjangoVerificationRepository(),
            notification_service=EmailNotificationService()
        )

        try:
            if service.confirm_password_reset(email, code, new_password):
                # Remove email da sessão
                if 'reset_email' in request.session:
                    del request.session['reset_email']

                messages.success(request, 'Senha redefinida com sucesso! Faça login com sua nova senha.')
                return redirect('accounts:login')
            else:
                messages.error(request, 'Código inválido ou expirado.')
        except ObjectDoesNotExist:
            messages.error(request, 'Email não encontrado.')
        except Exception as e:
            messages.error(request, 'Ocorreu um erro. Tente novamente.')

        return render(request, self.template_name, {'email': email})