# Forms para o app config

# Import dos formulários de email
from .email_forms import EmailConfigForm, EmailTestForm

# Import dos formulários de usuário
from .user_forms import UserCreateForm, UserUpdateForm

# Import dos formulários de sistema
try:
    from .system_config_forms import SystemConfigForm
except ImportError:
    pass

# Import dos formulários avançados
try:
    from .advanced_config_forms import *
except ImportError:
    pass
