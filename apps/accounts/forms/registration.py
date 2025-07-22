from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, HTML, Div
from crispy_forms.bootstrap import Field


class VerificationCodeWidget(forms.Widget):
    """Widget personalizado para código de verificação com 6 quadradinhos"""
    
    template_name = 'accounts/widgets/verification_code_widget.html'
    
    def __init__(self, attrs=None):
        super().__init__(attrs)
        if attrs is None:
            attrs = {}
        self.attrs = attrs.copy()
        self.attrs.update({
            'class': 'verification-code-input',
            'maxlength': '6',
            'pattern': '[0-9]{6}',
            'inputmode': 'numeric',
            'autocomplete': 'one-time-code'
        })
    
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['type'] = 'text'
        context['widget']['attrs']['placeholder'] = '123456'
        return context

User = get_user_model()

class RegistrationForm(UserCreationForm):
    """Formulário de registro de usuário"""

    email = forms.EmailField(
        label='E-mail',
        help_text='Digite um e-mail válido para receber o código de verificação.',
        widget=forms.EmailInput(attrs={
            'placeholder': 'seu@email.com',
            'autocomplete': 'email'
        })
    )
    first_name = forms.CharField(
        label='Nome',
        max_length=30,
        widget=forms.TextInput(attrs={
            'placeholder': 'Seu nome',
            'autocomplete': 'given-name'
        })
    )
    last_name = forms.CharField(
        label='Sobrenome',
        max_length=30,
        widget=forms.TextInput(attrs={
            'placeholder': 'Seu sobrenome',
            'autocomplete': 'family-name'
        })
    )
    username = forms.CharField(
        label='Nome de usuário',
        max_length=150,
        help_text='Escolha um nome único para identificar sua conta.',
        widget=forms.TextInput(attrs={
            'placeholder': 'nome_usuario',
            'autocomplete': 'username'
        })
    )
    password1 = forms.CharField(
        label='Senha',
        help_text='Sua senha deve ter pelo menos 8 caracteres.',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Digite sua senha',
            'autocomplete': 'new-password'
        })
    )
    password2 = forms.CharField(
        label='Confirmar senha',
        help_text='Digite a mesma senha novamente para confirmação.',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirme sua senha',
            'autocomplete': 'new-password'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'needs-validation'
        self.helper.attrs = {'novalidate': ''}

        self.helper.layout = Layout(
            HTML('<div class="row">'),
            Column('first_name', css_class='col-md-6'),
            Column('last_name', css_class='col-md-6'),
            HTML('</div>'),
            'email',
            'username',
            HTML('<div class="row">'),
            Column('password1', css_class='col-md-6'),
            Column('password2', css_class='col-md-6'),
            HTML('</div>'),
            HTML('<div class="d-grid gap-2 mt-4">'),
            Submit('submit', 'Criar Conta', css_class='btn btn-primary btn-lg'),
            HTML('</div>'),
            HTML('<div class="text-center mt-3">'),
            HTML('<p class="mb-0">Já tem uma conta? <a href="{% url \'accounts:login\' %}" class="text-decoration-none">Faça login</a></p>'),
            HTML('</div>')
        )

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password1', 'password2')

    def clean_email(self):
        """Valida se o email não está em uso por usuário verificado"""
        email = self.cleaned_data.get('email')
        if email:
            # Verifica se existe usuário verificado com este email
            if User.objects.filter(email__iexact=email, is_verified=True).exists():
                raise ValidationError('Já existe um usuário verificado com este e-mail.')
        return email

    def clean_username(self):
        """Valida se o username não está em uso"""
        username = self.cleaned_data.get('username')
        if username:
            if User.objects.filter(username__iexact=username).exists():
                raise ValidationError('Este nome de usuário já está em uso.')
        return username

class VerificationForm(forms.Form):
    """Formulário para verificação de código"""

    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={
            'readonly': True
        })
    )
    code = forms.CharField(
        label='Código de verificação',
        max_length=6,
        min_length=6,
        help_text='Digite o código de 6 dígitos enviado para seu e-mail.',
        widget=VerificationCodeWidget()
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'needs-validation'
        self.helper.attrs = {'novalidate': ''}

        self.helper.layout = Layout(
            'email',
            'code',
            HTML('<div class="d-grid gap-2 mt-4">'),
            Submit('submit', 'Verificar Código', css_class='btn btn-success btn-lg'),
            HTML('</div>'),
            HTML('<div class="text-center mt-3">'),
            HTML('<p class="mb-0">Não recebeu o código? <a href="#" class="text-decoration-none" onclick="resendCode()">Reenviar</a></p>'),
            HTML('</div>')
        )

    def clean_code(self):
        """Valida se o código tem apenas números"""
        code = self.cleaned_data.get('code')
        if code and not code.isdigit():
            raise ValidationError('O código deve conter apenas números.')
        return code