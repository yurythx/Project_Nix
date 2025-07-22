from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, HTML, Div, Field
from crispy_forms.bootstrap import FormActions

User = get_user_model()

class UserCreateForm(UserCreationForm):
    """Formulário para criação de usuários"""
    
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={
            'placeholder': 'usuario@exemplo.com'
        })
    )
    first_name = forms.CharField(
        label='Nome',
        max_length=30,
        widget=forms.TextInput(attrs={
            'placeholder': 'Nome'
        })
    )
    last_name = forms.CharField(
        label='Sobrenome',
        max_length=30,
        widget=forms.TextInput(attrs={
            'placeholder': 'Sobrenome'
        })
    )
    username = forms.CharField(
        label='Nome de usuário',
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'nome_usuario'
        })
    )
    is_active = forms.BooleanField(
        label='Ativo',
        required=False,
        initial=True,
        help_text='Usuário pode fazer login no sistema'
    )
    is_staff = forms.BooleanField(
        label='Staff',
        required=False,
        help_text='Permite acesso ao admin'
    )
    is_superuser = forms.BooleanField(
        label='Superusuário',
        required=False,
        help_text='Possui todas as permissões'
    )
    is_verified = forms.BooleanField(
        label='Verificado',
        required=False,
        initial=False,
        help_text='Usuário já está com email verificado.'
    )
    groups = forms.ModelMultipleChoiceField(
        label='Grupos',
        queryset=Group.objects.all(),
        required=False,
        help_text='Grupos de permissões para o usuário'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Adicionar autocomplete aos campos de senha
        self.fields['password1'].widget.attrs.update({
            'autocomplete': 'new-password'
        })
        self.fields['password2'].widget.attrs.update({
            'autocomplete': 'new-password'
        })

        # Adicionar autocomplete aos outros campos
        self.fields['email'].widget.attrs.update({
            'autocomplete': 'email'
        })
        self.fields['username'].widget.attrs.update({
            'autocomplete': 'username'
        })
        self.fields['first_name'].widget.attrs.update({
            'autocomplete': 'given-name'
        })
        self.fields['last_name'].widget.attrs.update({
            'autocomplete': 'family-name'
        })

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'needs-validation'
        self.helper.attrs = {'novalidate': ''}

        self.helper.layout = Layout(
            HTML('<div class="row">'),
            Column('first_name', css_class='col-md-6'),
            Column('last_name', css_class='col-md-6'),
            HTML('</div>'),
            HTML('<div class="row">'),
            Column('email', css_class='col-md-6'),
            Column('username', css_class='col-md-6'),
            HTML('</div>'),
            HTML('<div class="row">'),
            Column('password1', css_class='col-md-6'),
            Column('password2', css_class='col-md-6'),
            HTML('</div>'),
            HTML('<div class="card mt-4">'),
            HTML('<div class="card-header"><h6 class="mb-0">Permissões</h6></div>'),
            HTML('<div class="card-body">'),
            HTML('<div class="row">'),
            Column('is_active', css_class='col-md-3'),
            Column('is_staff', css_class='col-md-3'),
            Column('is_superuser', css_class='col-md-3'),
            Column('is_verified', css_class='col-md-3'),
            HTML('</div>'),
            'groups',
            HTML('</div>'),
            HTML('</div>'),
            FormActions(
                Submit('submit', 'Criar Usuário', css_class='btn btn-primary'),
                HTML('<a href="{% url \'config:user_list\' %}" class="btn btn-secondary ms-2">Cancelar</a>')
            )
        )

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 
                 'password1', 'password2', 'is_active', 'is_staff', 
                 'is_superuser', 'is_verified', 'groups')

    def clean_email(self):
        """Valida se o email não está em uso"""
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise ValidationError('Já existe um usuário com este e-mail.')
        return email

    def clean_username(self):
        """Valida se o username não está em uso"""
        username = self.cleaned_data.get('username')
        if username and User.objects.filter(username__iexact=username).exists():
            raise ValidationError('Já existe um usuário com este nome de usuário.')
        return username


class UserUpdateForm(forms.ModelForm):
    """Formulário para atualização de usuários"""
    
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={
            'class': 'form-control'
        })
    )
    first_name = forms.CharField(
        label='Nome',
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        })
    )
    last_name = forms.CharField(
        label='Sobrenome',
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        })
    )
    username = forms.CharField(
        label='Nome de usuário',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        })
    )
    is_active = forms.BooleanField(
        label='Ativo',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    is_staff = forms.BooleanField(
        label='Staff',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    is_superuser = forms.BooleanField(
        label='Superusuário',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    is_verified = forms.BooleanField(
        label='Verificado',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    groups = forms.ModelMultipleChoiceField(
        label='Grupos',
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        })
    )

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 
                 'is_active', 'is_staff', 'is_superuser', 'is_verified', 'groups')

    def __init__(self, *args, **kwargs):
        self.instance_id = kwargs.get('instance').id if kwargs.get('instance') else None
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
            HTML('<div class="row">'),
            Column('email', css_class='col-md-6'),
            Column('username', css_class='col-md-6'),
            HTML('</div>'),
            HTML('<div class="card mt-4">'),
            HTML('<div class="card-header"><h6 class="mb-0">Permissões</h6></div>'),
            HTML('<div class="card-body">'),
            HTML('<div class="row">'),
            Column('is_active', css_class='col-md-3'),
            Column('is_staff', css_class='col-md-3'),
            Column('is_superuser', css_class='col-md-3'),
            Column('is_verified', css_class='col-md-3'),
            HTML('</div>'),
            'groups',
            HTML('</div>'),
            HTML('</div>'),
            FormActions(
                Submit('submit', 'Atualizar Usuário', css_class='btn btn-primary'),
                HTML('<a href="{% url \'config:user_list\' %}" class="btn btn-secondary ms-2">Cancelar</a>')
            )
        )

    def clean_email(self):
        """Valida se o email não está em uso por outro usuário"""
        email = self.cleaned_data.get('email')
        if email:
            existing = User.objects.filter(email__iexact=email).exclude(id=self.instance_id)
            if existing.exists():
                raise ValidationError('Já existe um usuário com este e-mail.')
        return email

    def clean_username(self):
        """Valida se o username não está em uso por outro usuário"""
        username = self.cleaned_data.get('username')
        if username:
            existing = User.objects.filter(username__iexact=username).exclude(id=self.instance_id)
            if existing.exists():
                raise ValidationError('Já existe um usuário com este nome de usuário.')
        return username


class UserPermissionForm(forms.Form):
    """Formulário para gerenciar permissões de usuário"""
    
    permissions = forms.ModelMultipleChoiceField(
        label='Permissões',
        queryset=Permission.objects.all().select_related('content_type'),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        })
    )

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        
        if user:
            # Define permissões atuais como selecionadas
            self.fields['permissions'].initial = user.user_permissions.all()
        
        # Organiza permissões por app
        permissions = Permission.objects.all().select_related('content_type').order_by(
            'content_type__app_label', 'content_type__model', 'codename'
        )
        self.fields['permissions'].queryset = permissions


class UserSearchForm(forms.Form):
    """Formulário para busca de usuários"""

    query = forms.CharField(
        label='Buscar',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Nome, email ou username...'
        })
    )
    is_active = forms.ChoiceField(
        label='Status',
        choices=[
            ('', 'Todos'),
            ('true', 'Ativos'),
            ('false', 'Inativos')
        ],
        required=False
    )
    is_staff = forms.ChoiceField(
        label='Staff',
        choices=[
            ('', 'Todos'),
            ('true', 'Staff'),
            ('false', 'Não Staff')
        ],
        required=False
    )
    is_superuser = forms.ChoiceField(
        label='Superusuário',
        choices=[
            ('', 'Todos'),
            ('true', 'Superusuários'),
            ('false', 'Usuários normais')
        ],
        required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_class = 'row g-3'

        self.helper.layout = Layout(
            Column('query', css_class='col-md-6'),
            Column('is_active', css_class='col-md-2'),
            Column('is_staff', css_class='col-md-2'),
            Column('is_superuser', css_class='col-md-2'),
            HTML('<div class="col-12">'),
            Submit('submit', 'Buscar', css_class='btn btn-primary'),
            HTML('<a href="{% url \'config:user_list\' %}" class="btn btn-outline-secondary ms-2">Limpar</a>'),
            HTML('</div>')
        )
