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
                'placeholder': 'Nome do backup'
            }),
            'backup_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição opcional do backup'
            })
        }

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
        required=False,  # <- ADICIONAR ESTA LINHA
        validators=[
            FileExtensionValidator(allowed_extensions=['sql', 'json', 'tar', 'gz', 'zip'])
        ],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.sql,.json,.tar,.gz,.zip'
        })
    )
    
    confirm_restore = forms.BooleanField(
        label='Confirmo que desejo restaurar este backup',
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    backup_before_restore = forms.BooleanField(
        label='Criar backup antes da restauração',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

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