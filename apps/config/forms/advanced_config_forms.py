from django import forms
from django.conf import settings
from pathlib import Path
import datetime
import shutil

class EnvironmentVariablesForm(forms.Form):
    """Form para gerenciar variáveis de ambiente"""
    
    env_content = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 20,
            'cols': 80,
            'class': 'form-control',
            'placeholder': 'Digite as variáveis de ambiente no formato:\\nVARIAVEL=valor'
        }),
        required=False,
        help_text='Uma variável por linha no formato VARIAVEL=valor'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.load_current_env()
    
    def load_current_env(self):
        """Carrega o conteúdo atual do arquivo .env"""
        try:
            env_path = Path(settings.BASE_DIR) / '.env'
            if env_path.exists():
                with open(env_path, 'r', encoding='utf-8') as f:
                    self.fields['env_content'].initial = f.read()
        except Exception:
            pass
    
    def save(self, user=None):
        """Salva o conteúdo no arquivo .env"""
        try:
            env_path = Path(settings.BASE_DIR) / '.env'
            content = self.cleaned_data['env_content']
            
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
        except Exception:
            return False
    
    def create_backup(self):
        """Cria backup do arquivo .env atual"""
        try:
            env_path = Path(settings.BASE_DIR) / '.env'
            
            if not env_path.exists():
                return False, "Arquivo .env não existe"
            
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = env_path.parent / f'.env.backup.{timestamp}'
            
            shutil.copy2(env_path, backup_path)
            
            return True, backup_path.name
        except Exception as e:
            return False, str(e)