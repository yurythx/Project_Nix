# Forms para o app config

# Remover import do advanced_config_forms.py (arquivo será deletado)
from .multi_config_forms import EmailConfigurationForm, DatabaseConfigurationForm
from .backup_forms import BackupCreateForm, BackupUpdateForm, BackupRestoreForm
from .user_forms import UserCreateForm, UserUpdateForm
from .advanced_config_forms import EnvironmentVariablesForm  # Adicionado
# Removido: from .group_forms import GroupForm (arquivo não existe)

__all__ = [
    'EmailConfigurationForm',
    'DatabaseConfigurationForm', 
    'BackupCreateForm',
    'BackupUpdateForm',
    'BackupRestoreForm',  # Corrigido: era RestoreBackupForm
    'UserCreateForm',
    'UserUpdateForm',
    'EnvironmentVariablesForm',  # Adicionado
    # Removido: 'GroupForm'
]
