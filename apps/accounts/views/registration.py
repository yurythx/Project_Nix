from django.views import View
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from apps.accounts.forms.registration import RegistrationForm, VerificationForm
from apps.accounts.services.registration_service import RegistrationService
from apps.accounts.repositories.user_repository import DjangoUserRepository
from apps.accounts.repositories.verification_repository import DjangoVerificationRepository
from apps.accounts.notifications.email_notification import EmailNotificationService
from django.views.generic.edit import FormView

# Importação condicional do django-ratelimit
try:
    from django_ratelimit.decorators import ratelimit
    from django_ratelimit.exceptions import Ratelimited
    RATELIMIT_AVAILABLE = True
except ImportError:
    RATELIMIT_AVAILABLE = False
    # Decorator dummy para quando ratelimit não estiver disponível
    def ratelimit(key=None, rate=None, block=False):
        def decorator(func):
            return func
        return decorator

class RegistrationView(FormView):
    template_name = 'accounts/register.html'
    form_class = RegistrationForm
    success_url = reverse_lazy('accounts:verification')

    def form_valid(self, form):
        service = RegistrationService(
            user_repository=DjangoUserRepository(),
            verification_repository=DjangoVerificationRepository(),
            notification_service=EmailNotificationService()
        )
        try:
            user = service.register_user(
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                username=form.cleaned_data['username']
            )
            self.request.session['registration_email'] = user.email
            messages.success(
                self.request,
                f'Olá {user.first_name}! Código de verificação enviado para {user.email}. '
                'Verifique sua caixa de entrada e spam.'
            )
            return super().form_valid(form)
        except ValueError as e:
            error_msg = f'❌ Erro de validação: {str(e)}'
            messages.error(self.request, error_msg)
            form.add_error(None, str(e))
            return self.form_invalid(form)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Erro no registro: {str(e)}', exc_info=True)
            if 'email' in str(e).lower() or 'smtp' in str(e).lower() or 'template' in str(e).lower():
                error_msg = '📧 Erro ao enviar email de verificação. Verifique as configurações de email.'
            else:
                error_msg = f'🔧 Erro interno: {str(e)}. Tente novamente em alguns instantes.'
            messages.error(self.request, error_msg)
            form.add_error(None, 'Ocorreu um erro durante o registro. Tente novamente.')
            return self.form_invalid(form)

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'Você já está logado.')
            return redirect('pages:home')
        return super().get(request, *args, **kwargs)

@method_decorator(ratelimit(key='ip', rate='10/h', method='POST', block=True), name='post')
class VerificationView(View):
    """View para verificação de e-mail"""
    template_name = 'accounts/verify.html'
    form_class = VerificationForm
    
    def get(self, request):
        """Exibe o formulário de verificação"""
        if 'registration_email' not in request.session:
            messages.warning(request, 'Por favor, complete o registro primeiro.')
            return redirect('accounts:register')
            
        email = request.session['registration_email']
        form = self.form_class(initial={'email': email})
        return render(request, self.template_name, {'form': form, 'email': email})
    
    def post(self, request):
        """Processa o código de verificação"""
        form = self.form_class(request.POST)
        
        if form.is_valid():
            service = RegistrationService(
                user_repository=DjangoUserRepository(),
                verification_repository=DjangoVerificationRepository(),
                notification_service=EmailNotificationService()
            )
            
            email = form.cleaned_data['email']
            code = form.cleaned_data['code']
            
            try:
                if service.confirm_registration(email, code):
                    # Remove email da sessão após verificação
                    if 'registration_email' in request.session:
                        del request.session['registration_email']

                    messages.success(
                        request,
                        '🎉 Cadastro confirmado com sucesso! Sua conta foi ativada. Faça login para continuar.'
                    )
                    return redirect('accounts:login')
                else:
                    error_msg = 'Código inválido ou expirado. Verifique o código e tente novamente.'
                    messages.error(request, error_msg)
                    form.add_error('code', error_msg)
            except ObjectDoesNotExist:
                error_msg = 'E-mail não encontrado. Verifique se digitou corretamente.'
                messages.error(request, error_msg)
                form.add_error('email', error_msg)
            except Exception as e:
                error_msg = 'Ocorreu um erro durante a verificação. Tente novamente em alguns instantes.'
                messages.error(request, error_msg)
                form.add_error(None, error_msg)
        
        return render(request, self.template_name, {'form': form})