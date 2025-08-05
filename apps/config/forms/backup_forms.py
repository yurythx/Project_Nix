from django import forms
from django.core.validators import FileExtensionValidator
from ..models import BackupMetadata

class BackupCreateForm(forms.ModelForm):
    """Formulário para criação de backups"""
    
    class Meta:
        model = BackupMetadata
        fields = ['name', 'backup_type', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do backup',
                'required': True
            }),
            'backup_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição opcional do backup'
            })
        }
        labels = {
            'name': 'Nome do Backup',
            'backup_type': 'Tipo de Backup',
            'description': 'Descrição'
        }
        help_texts = {
            'name': 'Nome identificador para o backup',
            'backup_type': 'Selecione o tipo de dados para backup',
            'description': 'Descrição opcional para identificar o backup'
        }
    
    def clean_name(self):
        """Validação customizada para o nome do backup"""
        name = self.cleaned_data.get('name')
        if name:
            # Remover caracteres especiais que podem causar problemas
            import re
            if not re.match(r'^[a-zA-Z0-9\s\-_]+$', name):
                raise forms.ValidationError(
                    'O nome do backup deve conter apenas letras, números, espaços, hífens e underscores.'
                )
            if len(name.strip()) < 3:
                raise forms.ValidationError('O nome do backup deve ter pelo menos 3 caracteres.')
        return name.strip() if name else name

class BackupUpdateForm(forms.ModelForm):
    """Formulário para atualização de metadados de backup"""
    
    class Meta:
        model = BackupMetadata
        fields = ['name', 'description', 'status']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            })
        }

class BackupRestoreForm(forms.Form):
    """Formulário para restauração de backups"""
    
    backup_file = forms.FileField(
        label='Arquivo de Backup',
        required=False,
        validators=[
            FileExtensionValidator(allowed_extensions=['sql', 'json', 'tar', 'gz', 'zip', 'backup', 'sqlite3'])
        ],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.sql,.json,.tar,.gz,.zip,.backup,.sqlite3'
        }),
        help_text='Selecione um arquivo de backup válido (.sql, .json, .tar.gz, .zip, .backup, .sqlite3)'
    )
    
    confirm_restore = forms.BooleanField(
        label='Confirmo que desejo restaurar este backup',
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text='Esta ação irá sobrescrever os dados atuais'
    )
    
    backup_before_restore = forms.BooleanField(
        label='Criar backup antes da restauração',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text='Recomendado: cria um backup dos dados atuais antes da restauração'
    )
    
    def clean_backup_file(self):
        """Validação customizada para o arquivo de backup"""
        backup_file = self.cleaned_data.get('backup_file')
        if backup_file:
            # Verificar tamanho do arquivo (máximo 500MB)
            max_size = 500 * 1024 * 1024  # 500MB
            if backup_file.size > max_size:
                raise forms.ValidationError(
                    f'O arquivo é muito grande. Tamanho máximo permitido: 500MB. '
                    f'Tamanho do arquivo: {backup_file.size / (1024*1024):.1f}MB'
                )
            
            # Verificar extensão do arquivo
            allowed_extensions = ['.sql', '.json', '.tar', '.gz', '.zip', '.backup', '.sqlite3']
            file_extension = backup_file.name.lower().split('.')[-1]
            if f'.{file_extension}' not in allowed_extensions:
                raise forms.ValidationError(
                    f'Tipo de arquivo não suportado: .{file_extension}. '
                    f'Tipos permitidos: {', '.join(allowed_extensions)}'
                )
        
        return backup_file

class BackupDeleteForm(forms.Form):
    """Formulário para confirmação de exclusão de backup"""
    
    confirm_delete = forms.BooleanField(
        label='Confirmo que desejo excluir este backup permanentemente',
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    delete_file = forms.BooleanField(
        label='Excluir também o arquivo físico do backup',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )