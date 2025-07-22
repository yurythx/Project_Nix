from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Row, Column, Submit, HTML, Div
from crispy_forms.bootstrap import Field
import re

User = get_user_model()


class FlexibleLoginForm(AuthenticationForm):
    """
    Formulário de login que aceita email ou username
    """

    username = forms.CharField(
        label='E-mail ou Nome de Usuário',
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite seu e-mail ou nome de usuário',
            'autocomplete': 'username',
            'autofocus': True
        }),
        help_text='Você pode usar seu e-mail ou nome de usuário para fazer login'
    )

    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite sua senha',
            'autocomplete': 'current-password'
        })
    )

    remember_me = forms.BooleanField(
        label='Lembrar de mim',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text='Manter-me conectado neste dispositivo'
    )

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'needs-validation'
        self.helper.attrs = {'novalidate': ''}

        self.helper.layout = Layout(
            Fieldset(
                '🔐 Fazer Login',
                HTML('''
                    <div class="text-center mb-4">
                        <i class="fas fa-user-circle fa-3x text-primary mb-3"></i>
                        <p class="text-muted">Entre com seu e-mail ou nome de usuário</p>
                    </div>
                '''),
                Field('username', css_class='mb-3'),
                Field('password', css_class='mb-3'),
                Field('remember_me', css_class='mb-3'),
                css_class='mb-4'
            ),
            Div(
                Submit('submit', '🚀 Entrar', css_class='btn btn-primary btn-lg w-100 mb-3'),
                
                css_class='text-center'
            )
        )

        # Remover help_text padrão do Django
        self.fields['username'].help_text = 'Você pode usar seu e-mail ou nome de usuário'
        self.fields['password'].help_text = ''

    def clean_username(self):
        """Validação e normalização do campo username/email"""
        username_or_email = self.cleaned_data.get('username', '').strip()

        if not username_or_email:
            raise ValidationError('E-mail ou nome de usuário é obrigatório.')

        # Verificar se é um email válido
        if '@' in username_or_email:
            # Validar formato de email
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, username_or_email):
                raise ValidationError('Formato de e-mail inválido.')

            # Normalizar email (lowercase)
            username_or_email = username_or_email.lower()
        else:
            # Validar username
            if len(username_or_email) < 3:
                raise ValidationError('Nome de usuário deve ter pelo menos 3 caracteres.')

            # Verificar caracteres válidos para username
            if not re.match(r'^[a-zA-Z0-9._-]+$', username_or_email):
                raise ValidationError('Nome de usuário pode conter apenas letras, números, pontos, hífens e underscores.')

        return username_or_email

    def clean(self):
        """Validação geral do formulário"""
        username_or_email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username_or_email and password:
            # Tentar autenticar com username/email
            user = self.authenticate_user(username_or_email, password)

            if user is None:
                raise ValidationError(
                    'E-mail/usuário ou senha incorretos. Verifique seus dados e tente novamente.'
                )

            if not user.is_active:
                raise ValidationError(
                    'Esta conta está desativada. Entre em contato com o suporte.'
                )

            # Armazenar o usuário para uso posterior
            self.user_cache = user

        return self.cleaned_data

    def authenticate_user(self, username_or_email, password):
        """Autentica usuário por email ou username usando o backend personalizado"""

        # O backend personalizado já trata email e username automaticamente
        user = authenticate(
            self.request,
            username=username_or_email,
            password=password
        )

        return user

    def get_user(self):
        """Retorna o usuário autenticado"""
        return getattr(self, 'user_cache', None)


class QuickLoginForm(forms.Form):
    """
    Formulário simplificado para login rápido
    """

    login = forms.CharField(
        label='E-mail ou Usuário',
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'E-mail ou usuário',
            'autocomplete': 'username'
        })
    )

    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Senha',
            'autocomplete': 'current-password'
        })
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'quick-login-form'
        self.helper.form_show_labels = False

        self.helper.layout = Layout(
            Row(
                Column('login', css_class='col-md-4'),
                Column('password', css_class='col-md-4'),
                Column(
                    Submit('submit', 'Entrar', css_class='btn btn-primary btn-sm'),
                    css_class='col-md-4 d-grid'
                ),
                css_class='g-2 align-items-end'
            )
        )

    def clean(self):
        """Validação do formulário rápido"""
        login = self.cleaned_data.get('login', '').strip()
        password = self.cleaned_data.get('password')

        if login and password:
            # Usar a mesma lógica do FlexibleLoginForm
            form = FlexibleLoginForm(request=self.request)
            user = form.authenticate_user(login, password)

            if user is None:
                raise ValidationError('Credenciais inválidas.')

            if not user.is_active:
                raise ValidationError('Conta desativada.')

            self.user_cache = user

        return self.cleaned_data

    def get_user(self):
        """Retorna o usuário autenticado"""
        return getattr(self, 'user_cache', None)