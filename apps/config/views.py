# Importa views da pasta views
from .views.dashboard import ConfigDashboardView
from .views.user_views import UserListView, UserCreateView, UserDetailView, UserUpdateView, UserDeleteView
from .views.system_config_views import SystemConfigView

__all__ = [
    'ConfigDashboardView',
    'UserListView',
    'UserCreateView',
    'UserDetailView',
    'UserUpdateView',
    'UserDeleteView',
    'SystemConfigView',
]
