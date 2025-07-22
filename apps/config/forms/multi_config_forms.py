from django import forms
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Row, Column, Submit, HTML, Div
from crispy_forms.bootstrap import Field
from apps.config.models import EmailConfiguration, DatabaseConfiguration


class EmailConfigurationForm(forms.ModelForm):
    """Formulário para configurações de email"""
    
    class Meta:
        model = EmailConfiguration
        fields = [
            'name', 'description', 'email_backend', 'email_host', 'email_port',
            'email_host_user', 'email_host_password', 'email_use_tls', 'email_use_ssl',
            'default_from_email', 'email_timeout', 'is_active', 'is_default'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Ex: Gmail Principal, Outlook Backup'
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Descrição opcional desta configuração'
            }),
            'email_host': forms.TextInput(attrs={
                'placeholder': 'smtp.gmail.com'
            }),
            'email_host_user': forms.EmailInput(attrs={
                'placeholder': 'seu-email@gmail.com'
            }),
            'email_host_password': forms.PasswordInput(attrs={
                'placeholder': 'Senha ou senha de app'
            }),
            'default_from_email': forms.EmailInput(attrs={
                'placeholder': 'noreply@seusite.com'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'needs-validation'
        self.helper.attrs = {'novalidate': ''}
        
        self.helper.layout = Layout(
            Fieldset(
                '📧 Informações Básicas',
                Row(
                    Column('name', css_class='col-md-8'),
                    Column('is_active', css_class='col-md-2'),
                    Column('is_default', css_class='col-md-2'),
                ),
                'description',
                css_class='mb-4'
            ),
            
            Fieldset(
                '🔧 Configurações SMTP',
                HTML('''
                    <div class="row mb-3">
                        <div class="col-md-12">
                            <div class="btn-group" role="group">
                                <button type="button" class="btn btn-outline-danger btn-sm" onclick="fillGmailConfig()">
                                    <i class="fab fa-google me-1"></i>Gmail
                                </button>
                                <button type="button" class="btn btn-outline-primary btn-sm" onclick="fillOutlookConfig()">
                                    <i class="fab fa-microsoft me-1"></i>Outlook
                                </button>
                                <button type="button" class="btn btn-outline-success btn-sm" onclick="fillSendGridConfig()">
                                    <i class="fas fa-paper-plane me-1"></i>SendGrid
                                </button>
                            </div>
                        </div>
                    </div>
                '''),
                'email_backend',
                Row(
                    Column('email_host', css_class='col-md-8'),
                    Column('email_port', css_class='col-md-4'),
                ),
                Row(
                    Column('email_host_user', css_class='col-md-6'),
                    Column('email_host_password', css_class='col-md-6'),
                ),
                Row(
                    Column('email_use_tls', css_class='col-md-4'),
                    Column('email_use_ssl', css_class='col-md-4'),
                    Column('email_timeout', css_class='col-md-4'),
                ),
                'default_from_email',
                css_class='mb-4'
            ),
            
            Div(
                Row(
                    Column(
                        HTML('<a href="{% url \'config:email_configs\' %}" class="btn btn-secondary">Cancelar</a>'),
                        css_class='col-md-6'
                    ),
                    Column(
                        Submit('submit', 'Salvar Configuração', css_class='btn btn-primary w-100'),
                        css_class='col-md-6'
                    ),
                ),
                css_class='text-end'
            )
        )
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validar TLS e SSL
        use_tls = cleaned_data.get('email_use_tls')
        use_ssl = cleaned_data.get('email_use_ssl')
        
        if use_tls and use_ssl:
            raise ValidationError('Não é possível usar TLS e SSL simultaneamente.')
        
        # Validar porta baseada no protocolo
        port = cleaned_data.get('email_port')
        if port:
            if use_ssl and port not in [465, 587]:
                self.add_error('email_port', 'Para SSL, use geralmente a porta 465.')
            elif use_tls and port not in [587, 25]:
                self.add_error('email_port', 'Para TLS, use geralmente a porta 587.')
        
        return cleaned_data


class DatabaseConfigurationForm(forms.ModelForm):
    """Formulário para configurações de banco de dados"""
    
    class Meta:
        model = DatabaseConfiguration
        fields = [
            'name', 'description', 'engine', 'name_db', 'user', 'password',
            'host', 'port', 'options', 'is_active', 'is_default'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Ex: PostgreSQL Principal, MySQL Backup'
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Descrição opcional desta configuração'
            }),
            'name_db': forms.TextInput(attrs={
                'placeholder': 'nome_do_banco'
            }),
            'user': forms.TextInput(attrs={
                'placeholder': 'usuario_db'
            }),
            'password': forms.PasswordInput(attrs={
                'placeholder': 'senha_do_usuario'
            }),
            'host': forms.TextInput(attrs={
                'placeholder': 'localhost'
            }),
            'port': forms.TextInput(attrs={
                'placeholder': '5432'
            }),
            'options': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': '{"sslmode": "require", "charset": "utf8"}'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'needs-validation'
        
        self.helper.layout = Layout(
            Fieldset(
                '🗄️ Informações Básicas',
                Row(
                    Column('name', css_class='col-md-8'),
                    Column('is_active', css_class='col-md-2'),
                    Column('is_default', css_class='col-md-2'),
                ),
                'description',
                css_class='mb-4'
            ),
            
            Fieldset(
                '⚙️ Configurações do Banco',
                HTML('''
                    <div class="row mb-3">
                        <div class="col-md-12">
                            <div class="btn-group" role="group">
                                <button type="button" class="btn btn-outline-info btn-sm" onclick="fillPostgreSQLConfig()">
                                    <i class="fas fa-database me-1"></i>PostgreSQL
                                </button>
                                <button type="button" class="btn btn-outline-warning btn-sm" onclick="fillMySQLConfig()">
                                    <i class="fas fa-database me-1"></i>MySQL
                                </button>
                                <button type="button" class="btn btn-outline-secondary btn-sm" onclick="fillSQLiteConfig()">
                                    <i class="fas fa-file-alt me-1"></i>SQLite
                                </button>
                            </div>
                        </div>
                    </div>
                '''),
                'engine',
                'name_db',
                Row(
                    Column('user', css_class='col-md-6'),
                    Column('password', css_class='col-md-6'),
                ),
                Row(
                    Column('host', css_class='col-md-8'),
                    Column('port', css_class='col-md-4'),
                ),
                Field('options', css_class='font-monospace'),
                css_class='mb-4'
            ),
            
            Div(
                Row(
                    Column(
                        HTML('<a href="{% url \'config:database_configs\' %}" class="btn btn-secondary">Cancelar</a>'),
                        css_class='col-md-6'
                    ),
                    Column(
                        Submit('submit', 'Salvar Configuração', css_class='btn btn-primary w-100'),
                        css_class='col-md-6'
                    ),
                ),
                css_class='text-end'
            )
        )
    
    def clean_options(self):
        """Validar JSON das opções"""
        import json

        options = self.cleaned_data.get('options')
        if options:
            try:
                if isinstance(options, str):
                    json.loads(options)
            except json.JSONDecodeError:
                raise ValidationError('Opções devem estar em formato JSON válido.')
        return options
    
    def clean(self):
        cleaned_data = super().clean()
        engine = cleaned_data.get('engine')
        
        # Validações específicas por engine
        if engine == 'django.db.backends.sqlite3':
            # SQLite não precisa de user, password, host, port
            cleaned_data['user'] = ''
            cleaned_data['password'] = ''
            cleaned_data['host'] = ''
            cleaned_data['port'] = ''
        else:
            # Outros bancos precisam de user
            if not cleaned_data.get('user'):
                self.add_error('user', 'Usuário é obrigatório para este tipo de banco.')
        
        return cleaned_data


class ConfigurationTestForm(forms.Form):
    """Formulário para testar configurações"""
    
    test_email = forms.EmailField(
        label='Email para Teste',
        required=False,
        widget=forms.EmailInput(attrs={
            'placeholder': 'seu-email@exemplo.com'
        }),
        help_text='Email que receberá o teste (opcional)'
    )
    
    def __init__(self, config_type='email', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config_type = config_type
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'test-form'
        
        if config_type == 'email':
            self.helper.layout = Layout(
                Fieldset(
                    '🧪 Teste de Email',
                    'test_email',
                    HTML('''
                        <div class="d-grid gap-2 d-md-flex">
                            <button type="submit" name="action" value="test_connection" class="btn btn-outline-primary">
                                <i class="fas fa-plug me-2"></i>Testar Conexão
                            </button>
                            <button type="submit" name="action" value="send_test" class="btn btn-primary">
                                <i class="fas fa-paper-plane me-2"></i>Enviar Email Teste
                            </button>
                        </div>
                    '''),
                )
            )
        else:  # database
            self.helper.layout = Layout(
                Fieldset(
                    '🧪 Teste de Banco de Dados',
                    HTML('''
                        <div class="d-grid">
                            <button type="submit" name="action" value="test_connection" class="btn btn-primary">
                                <i class="fas fa-database me-2"></i>Testar Conexão
                            </button>
                        </div>
                    '''),
                )
            )
