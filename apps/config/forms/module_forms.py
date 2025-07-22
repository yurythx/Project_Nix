from django import forms
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Row, Column, Submit, Reset, HTML, Div
from crispy_forms.bootstrap import FormActions
from apps.config.models.app_module_config import AppModuleConfiguration
import json


class ModuleConfigurationForm(forms.ModelForm):
    """Formulário para configuração de módulos"""
    
    class Meta:
        model = AppModuleConfiguration
        fields = [
            'display_name', 'description', 'module_type', 'status',
            'url_pattern', 'menu_icon', 'menu_order', 'show_in_menu',
            'dependencies', 'required_permissions', 'module_settings',
            'version', 'author', 'documentation_url'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'dependencies': forms.Textarea(attrs={'rows': 3, 'placeholder': '["app1", "app2"]'}),
            'required_permissions': forms.Textarea(attrs={'rows': 3, 'placeholder': '["permission1", "permission2"]'}),
            'module_settings': forms.Textarea(attrs={'rows': 4, 'placeholder': '{"setting1": "value1"}'}),
            'menu_icon': forms.TextInput(attrs={'placeholder': 'fas fa-puzzle-piece'}),
            'url_pattern': forms.TextInput(attrs={'placeholder': 'app_name/'}),
            'documentation_url': forms.URLInput(attrs={'placeholder': 'https://docs.example.com'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Desabilita campos para módulos principais
        if self.instance and self.instance.is_core:
            self.fields['module_type'].disabled = True
            self.fields['status'].disabled = True
            
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-django'
        
        self.helper.layout = Layout(
            HTML('<div class="row">'),
            HTML('<div class="col-lg-8">'),
            
            # Informações Básicas
            Fieldset(
                'Informações Básicas',
                Row(
                    Column('display_name', css_class='col-md-8'),
                    Column('module_type', css_class='col-md-4'),
                ),
                'description',
                Row(
                    Column('status', css_class='col-md-6'),
                    Column('version', css_class='col-md-6'),
                ),
                css_class='card-django border-0 shadow-sm mb-4'
            ),
            
            # Configurações de Menu
            Fieldset(
                'Configurações de Menu',
                Row(
                    Column('menu_icon', css_class='col-md-6'),
                    Column('menu_order', css_class='col-md-6'),
                ),
                Row(
                    Column('url_pattern', css_class='col-md-8'),
                    Column('show_in_menu', css_class='col-md-4'),
                ),
                css_class='card-django border-0 shadow-sm mb-4'
            ),
            
            # Dependências e Permissões
            Fieldset(
                'Dependências e Permissões',
                'dependencies',
                'required_permissions',
                css_class='card-django border-0 shadow-sm mb-4'
            ),
            
            HTML('</div>'),
            HTML('<div class="col-lg-4">'),
            
            # Configurações Avançadas
            Fieldset(
                'Configurações Avançadas',
                'module_settings',
                css_class='card-django border-0 shadow-sm mb-4'
            ),
            
            # Metadados
            Fieldset(
                'Metadados',
                'author',
                'documentation_url',
                css_class='card-django border-0 shadow-sm mb-4'
            ),
            
            HTML('</div>'),
            HTML('</div>'),
            
            # Botões de Ação
            FormActions(
                Submit('save', 'Salvar Configurações', css_class='btn btn-primary btn-lg'),
                Reset('reset', 'Limpar', css_class='btn btn-outline-secondary btn-lg'),
                HTML('<a href="{% url \'config:module_list\' %}" class="btn btn-outline-primary btn-lg">Voltar</a>'),
                css_class='text-center mt-4'
            )
        )
    
    def clean_dependencies(self):
        """Valida o campo dependencies"""
        dependencies = self.cleaned_data.get('dependencies')
        
        if dependencies:
            try:
                if isinstance(dependencies, str):
                    dependencies = json.loads(dependencies)
                
                if not isinstance(dependencies, list):
                    raise ValidationError('Dependências devem ser uma lista.')
                
                for dep in dependencies:
                    if not isinstance(dep, str):
                        raise ValidationError('Cada dependência deve ser uma string.')
                
                return dependencies
            except json.JSONDecodeError:
                raise ValidationError('Formato JSON inválido para dependências.')
        
        return dependencies or []
    
    def clean_required_permissions(self):
        """Valida o campo required_permissions"""
        permissions = self.cleaned_data.get('required_permissions')
        
        if permissions:
            try:
                if isinstance(permissions, str):
                    permissions = json.loads(permissions)
                
                if not isinstance(permissions, list):
                    raise ValidationError('Permissões devem ser uma lista.')
                
                for perm in permissions:
                    if not isinstance(perm, str):
                        raise ValidationError('Cada permissão deve ser uma string.')
                
                return permissions
            except json.JSONDecodeError:
                raise ValidationError('Formato JSON inválido para permissões.')
        
        return permissions or []
    
    def clean_module_settings(self):
        """Valida o campo module_settings"""
        settings = self.cleaned_data.get('module_settings')
        
        if settings:
            try:
                if isinstance(settings, str):
                    settings = json.loads(settings)
                
                if not isinstance(settings, dict):
                    raise ValidationError('Configurações devem ser um objeto JSON.')
                
                return settings
            except json.JSONDecodeError:
                raise ValidationError('Formato JSON inválido para configurações.')
        
        return settings or {}
    
    def clean(self):
        """Validações gerais do formulário"""
        cleaned_data = super().clean()
        
        # Não permite alterar status de módulos principais para inativo
        if self.instance and self.instance.is_core:
            if cleaned_data.get('status') != 'active':
                raise ValidationError('Módulos principais devem permanecer ativos.')
        
        return cleaned_data


class ModuleToggleForm(forms.Form):
    """Formulário simples para habilitar/desabilitar módulos"""
    
    action = forms.ChoiceField(
        choices=[
            ('enable', 'Habilitar'),
            ('disable', 'Desabilitar'),
        ],
        widget=forms.HiddenInput()
    )
    
    def __init__(self, module, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.module = module
        
        # Define a ação baseada no status atual
        if module.is_enabled:
            self.fields['action'].initial = 'disable'
        else:
            self.fields['action'].initial = 'enable'
    
    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        
        # Não permite desabilitar módulos principais
        if action == 'disable' and self.module.is_core:
            raise ValidationError('Módulos principais não podem ser desabilitados.')
        
        return cleaned_data


class ModuleCreateForm(forms.ModelForm):
    """Formulário para criar novos módulos"""
    
    class Meta:
        model = AppModuleConfiguration
        fields = [
            'app_name', 'display_name', 'description', 'module_type',
            'url_pattern', 'menu_icon', 'menu_order', 'show_in_menu',
            'version', 'author'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'menu_icon': forms.TextInput(attrs={'placeholder': 'fas fa-puzzle-piece'}),
            'url_pattern': forms.TextInput(attrs={'placeholder': 'app_name/'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-django'
        
        self.helper.layout = Layout(
            Fieldset(
                'Novo Módulo',
                Row(
                    Column('app_name', css_class='col-md-6'),
                    Column('display_name', css_class='col-md-6'),
                ),
                'description',
                Row(
                    Column('module_type', css_class='col-md-6'),
                    Column('url_pattern', css_class='col-md-6'),
                ),
                Row(
                    Column('menu_icon', css_class='col-md-4'),
                    Column('menu_order', css_class='col-md-4'),
                    Column('show_in_menu', css_class='col-md-4'),
                ),
                Row(
                    Column('version', css_class='col-md-6'),
                    Column('author', css_class='col-md-6'),
                ),
            ),
            FormActions(
                Submit('save', 'Criar Módulo', css_class='btn btn-success btn-lg'),
                HTML('<a href="{% url \'config:module_list\' %}" class="btn btn-outline-secondary btn-lg">Cancelar</a>'),
                css_class='text-center mt-4'
            )
        )
    
    def clean_app_name(self):
        """Valida o nome do app"""
        app_name = self.cleaned_data.get('app_name')
        
        if app_name:
            # Verifica se já existe
            if AppModuleConfiguration.objects.filter(app_name=app_name).exists():
                raise ValidationError('Já existe um módulo com este nome.')
            
            # Valida formato
            if not app_name.isalnum() and '_' not in app_name:
                raise ValidationError('Nome do app deve conter apenas letras, números e underscore.')
        
        return app_name
