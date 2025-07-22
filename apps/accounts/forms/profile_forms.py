from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Row, Column, Submit, HTML, Div
from crispy_forms.bootstrap import Field
import re
from datetime import date, timedelta

User = get_user_model()

class ProfileUpdateForm(forms.ModelForm):
    """Formulário para atualização do perfil do usuário"""
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'bio', 'phone', 
            'birth_date', 'location'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'placeholder': 'Digite seu nome',
                'class': 'form-control'
            }),
            'last_name': forms.TextInput(attrs={
                'placeholder': 'Digite seu sobrenome',
                'class': 'form-control'
            }),
            'bio': forms.Textarea(attrs={
                'placeholder': 'Conte um pouco sobre você...',
                'rows': 4,
                'class': 'form-control'
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': '(11) 99999-9999',
                'class': 'form-control'
            }),
            'birth_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'location': forms.TextInput(attrs={
                'placeholder': 'Cidade, Estado',
                'class': 'form-control'
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
                '👤 Informações Pessoais',
                Row(
                    Column('first_name', css_class='form-group col-md-6 mb-3'),
                    Column('last_name', css_class='form-group col-md-6 mb-3'),
                    css_class='form-row'
                ),
                Field('bio', css_class='mb-3'),
                css_class='mb-4'
            ),
            Fieldset(
                '📞 Informações de Contato',
                Row(
                    Column('phone', css_class='form-group col-md-6 mb-3'),
                    Column('location', css_class='form-group col-md-6 mb-3'),
                    css_class='form-row'
                ),
                Field('birth_date', css_class='mb-3'),
                css_class='mb-4'
            ),
            Div(
                Submit('submit', '💾 Salvar Alterações', css_class='btn btn-primary btn-lg'),
                HTML('<a href="{% url "accounts:profile" %}" class="btn btn-outline-secondary btn-lg ms-2">❌ Cancelar</a>'),
                css_class='text-center'
            )
        )
        
        # Adicionar classes de validação
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
            if field.required:
                field.widget.attrs.update({'required': 'required'})

    def clean_first_name(self):
        """Validação do nome"""
        first_name = self.cleaned_data.get('first_name', '').strip()

        if first_name:
            # Verificar se contém apenas letras e espaços
            if not re.match(r'^[a-zA-ZÀ-ÿ\s]+$', first_name):
                raise forms.ValidationError('O nome deve conter apenas letras e espaços.')

            # Verificar comprimento
            if len(first_name) < 2:
                raise forms.ValidationError('O nome deve ter pelo menos 2 caracteres.')

            if len(first_name) > 30:
                raise forms.ValidationError('O nome deve ter no máximo 30 caracteres.')

        return first_name

    def clean_last_name(self):
        """Validação do sobrenome"""
        last_name = self.cleaned_data.get('last_name', '').strip()

        if last_name:
            # Verificar se contém apenas letras e espaços
            if not re.match(r'^[a-zA-ZÀ-ÿ\s]+$', last_name):
                raise forms.ValidationError('O sobrenome deve conter apenas letras e espaços.')

            # Verificar comprimento
            if len(last_name) < 2:
                raise forms.ValidationError('O sobrenome deve ter pelo menos 2 caracteres.')

            if len(last_name) > 30:
                raise forms.ValidationError('O sobrenome deve ter no máximo 30 caracteres.')

        return last_name

    def clean_phone(self):
        """Validação do telefone"""
        phone = self.cleaned_data.get('phone', '').strip()

        if phone:
            # Remover caracteres não numéricos para validação
            phone_digits = re.sub(r'\D', '', phone)

            # Verificar se tem 10 ou 11 dígitos (telefone brasileiro)
            if len(phone_digits) not in [10, 11]:
                raise forms.ValidationError('Telefone deve ter 10 ou 11 dígitos.')

            # Verificar se não são todos os dígitos iguais
            if len(set(phone_digits)) == 1:
                raise forms.ValidationError('Telefone inválido.')

            # Formatar o telefone
            if len(phone_digits) == 11:
                phone = f'({phone_digits[:2]}) {phone_digits[2:7]}-{phone_digits[7:]}'
            else:
                phone = f'({phone_digits[:2]}) {phone_digits[2:6]}-{phone_digits[6:]}'

        return phone

    def clean_birth_date(self):
        """Validação da data de nascimento"""
        birth_date = self.cleaned_data.get('birth_date')

        if birth_date:
            today = date.today()

            # Verificar se não é uma data futura
            if birth_date > today:
                raise forms.ValidationError('A data de nascimento não pode ser no futuro.')

            # Verificar idade mínima (13 anos)
            min_date = today - timedelta(days=13*365)
            if birth_date > min_date:
                raise forms.ValidationError('Você deve ter pelo menos 13 anos.')

            # Verificar idade máxima (120 anos)
            max_date = today - timedelta(days=120*365)
            if birth_date < max_date:
                raise forms.ValidationError('Data de nascimento inválida.')

        return birth_date

    def clean_location(self):
        """Validação da localização"""
        location = self.cleaned_data.get('location', '').strip()

        if location:
            # Verificar se contém apenas letras, espaços, vírgulas e hífens
            if not re.match(r'^[a-zA-ZÀ-ÿ\s,\-]+$', location):
                raise forms.ValidationError('Localização deve conter apenas letras, espaços, vírgulas e hífens.')

            # Verificar comprimento
            if len(location) < 3:
                raise forms.ValidationError('Localização deve ter pelo menos 3 caracteres.')

            if len(location) > 100:
                raise forms.ValidationError('Localização deve ter no máximo 100 caracteres.')

        return location

    def clean_bio(self):
        """Validação da biografia"""
        bio = self.cleaned_data.get('bio', '').strip()

        if bio:
            # Verificar comprimento
            if len(bio) > 500:
                raise forms.ValidationError('A biografia deve ter no máximo 500 caracteres.')

            # Verificar se não contém apenas espaços ou caracteres especiais
            if not re.search(r'[a-zA-ZÀ-ÿ0-9]', bio):
                raise forms.ValidationError('A biografia deve conter pelo menos uma letra ou número.')

        return bio

class AvatarUpdateForm(forms.ModelForm):
    """Formulário para atualização do avatar do usuário"""
    
    class Meta:
        model = User
        fields = ['avatar']
        widgets = {
            'avatar': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.form_class = 'avatar-form'
        
        self.helper.layout = Layout(
            Fieldset(
                '📸 Foto de Perfil',
                HTML('''
                    <div class="text-center mb-4">
                        <div class="avatar-preview mb-3">
                            {% if user.avatar %}
                                <img src="{{ user.get_avatar_url }}" class="rounded-circle" width="150" height="150" alt="Avatar atual" id="avatar-preview">
                            {% else %}
                                <img src="{{ user.get_default_avatar }}" class="rounded-circle" width="150" height="150" alt="Avatar padrão" id="avatar-preview">
                            {% endif %}
                        </div>
                        <p class="text-muted small">
                            <i class="fas fa-info-circle me-1"></i>
                            Formatos aceitos: JPG, PNG, GIF. Tamanho máximo: 5MB
                        </p>
                    </div>
                '''),
                Field('avatar', css_class='mb-3'),
                css_class='mb-4'
            ),
            Div(
                Submit('submit', '📸 Atualizar Foto', css_class='btn btn-success btn-lg'),
                HTML('<button type="button" class="btn btn-outline-danger btn-lg ms-2" onclick="removeAvatar()">🗑️ Remover Foto</button>'),
                css_class='text-center'
            )
        )
    
    def clean_avatar(self):
        """Validação personalizada para o avatar"""
        avatar = self.cleaned_data.get('avatar')
        
        if avatar:
            # Verificar tamanho do arquivo (5MB máximo)
            if avatar.size > 5 * 1024 * 1024:
                raise forms.ValidationError('O arquivo é muito grande. Tamanho máximo: 5MB.')
            
            # Verificar tipo do arquivo
            valid_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if avatar.content_type not in valid_types:
                raise forms.ValidationError('Formato de arquivo não suportado. Use JPG, PNG, GIF ou WebP.')
        
        return avatar

class EmailUpdateForm(forms.ModelForm):
    """Formulário para atualização do email do usuário"""
    
    current_password = forms.CharField(
        label='Senha Atual',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Digite sua senha atual',
            'class': 'form-control',
            'autocomplete': 'current-password'
        }),
        help_text='Por segurança, confirme sua senha atual'
    )
    
    class Meta:
        model = User
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={
                'placeholder': 'novo@email.com',
                'class': 'form-control'
            })
        }
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'needs-validation'
        
        self.helper.layout = Layout(
            Fieldset(
                '📧 Alterar E-mail',
                HTML(f'''
                    <div class="alert alert-info mb-3">
                        <i class="fas fa-info-circle me-2"></i>
                        <strong>E-mail atual:</strong> {user.email}
                    </div>
                '''),
                Field('email', css_class='mb-3'),
                Field('current_password', css_class='mb-3'),
                HTML('''
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        <strong>Atenção:</strong> Você receberá um código de verificação no novo e-mail.
                    </div>
                '''),
                css_class='mb-4'
            ),
            Div(
                Submit('submit', '📧 Alterar E-mail', css_class='btn btn-warning btn-lg'),
                HTML('<a href="{% url "accounts:profile" %}" class="btn btn-outline-secondary btn-lg ms-2">❌ Cancelar</a>'),
                css_class='text-center'
            )
        )
    
    def clean_current_password(self):
        """Valida a senha atual"""
        password = self.cleaned_data.get('current_password')
        if not self.user.check_password(password):
            raise forms.ValidationError('Senha atual incorreta.')
        return password
    
    def clean_email(self):
        """Valida o novo email"""
        email = self.cleaned_data.get('email', '').strip().lower()

        if not email:
            raise forms.ValidationError('E-mail é obrigatório.')

        # Validação básica de formato
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            raise forms.ValidationError('Formato de e-mail inválido.')

        # Verificar se é diferente do atual
        if email == self.user.email.lower():
            raise forms.ValidationError('O novo e-mail deve ser diferente do atual.')

        # Verificar se o email já está em uso
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Este e-mail já está sendo usado por outro usuário.')

        # Verificar domínios bloqueados (opcional)
        blocked_domains = ['tempmail.com', '10minutemail.com', 'guerrillamail.com']
        domain = email.split('@')[1].lower()
        if domain in blocked_domains:
            raise forms.ValidationError('Este domínio de e-mail não é permitido.')

        return email

class PasswordChangeForm(forms.Form):
    """Formulário para alteração de senha"""
    
    current_password = forms.CharField(
        label='Senha Atual',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Digite sua senha atual',
            'class': 'form-control',
            'autocomplete': 'current-password'
        })
    )
    new_password1 = forms.CharField(
        label='Nova Senha',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Digite a nova senha',
            'class': 'form-control',
            'autocomplete': 'new-password'
        }),
        help_text='Mínimo 8 caracteres, com letras e números'
    )
    new_password2 = forms.CharField(
        label='Confirmar Nova Senha',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirme a nova senha',
            'class': 'form-control',
            'autocomplete': 'new-password'
        })
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'needs-validation'
        
        self.helper.layout = Layout(
            Fieldset(
                '🔒 Alterar Senha',
                Field('current_password', css_class='mb-3'),
                Field('new_password1', css_class='mb-3'),
                Field('new_password2', css_class='mb-3'),
                css_class='mb-4'
            ),
            Div(
                Submit('submit', '🔒 Alterar Senha', css_class='btn btn-danger btn-lg'),
                HTML('<a href="{% url "accounts:profile" %}" class="btn btn-outline-secondary btn-lg ms-2">❌ Cancelar</a>'),
                css_class='text-center'
            )
        )
    
    def clean_current_password(self):
        """Valida a senha atual"""
        password = self.cleaned_data.get('current_password')
        if not self.user.check_password(password):
            raise forms.ValidationError('Senha atual incorreta.')
        return password
    
    def clean_new_password2(self):
        """Valida se as senhas coincidem"""
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError('As senhas não coincidem.')
        
        return password2
    
    def clean_new_password1(self):
        """Valida a nova senha"""
        password = self.cleaned_data.get('new_password1', '')

        if not password:
            raise forms.ValidationError('Nova senha é obrigatória.')

        # Verificar comprimento mínimo
        if len(password) < 8:
            raise forms.ValidationError('A senha deve ter pelo menos 8 caracteres.')

        # Verificar comprimento máximo
        if len(password) > 128:
            raise forms.ValidationError('A senha deve ter no máximo 128 caracteres.')

        # Verificar se não contém apenas números
        if password.isdigit():
            raise forms.ValidationError('A senha não pode conter apenas números.')

        # Verificar se contém pelo menos uma letra
        if not re.search(r'[a-zA-Z]', password):
            raise forms.ValidationError('A senha deve conter pelo menos uma letra.')

        # Verificar se contém pelo menos um número
        if not re.search(r'\d', password):
            raise forms.ValidationError('A senha deve conter pelo menos um número.')

        # Verificar se não é igual ao email
        if password.lower() == self.user.email.lower():
            raise forms.ValidationError('A senha não pode ser igual ao seu e-mail.')

        # Verificar se não é igual ao nome de usuário
        if password.lower() == self.user.username.lower():
            raise forms.ValidationError('A senha não pode ser igual ao seu nome de usuário.')

        # Verificar senhas comuns
        common_passwords = [
            '12345678', 'password', 'senha123', 'admin123',
            'qwerty123', '123456789', 'password123'
        ]
        if password.lower() in common_passwords:
            raise forms.ValidationError('Esta senha é muito comum. Escolha uma senha mais segura.')

        # Verificar se não contém espaços
        if ' ' in password:
            raise forms.ValidationError('A senha não pode conter espaços.')

        return password
