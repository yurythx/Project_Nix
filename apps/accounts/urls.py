from django.urls import path
from apps.accounts.views import (
    RegistrationView,
    VerificationView,
    LoginView,
    LogoutView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    UserProfileView,
    UserUpdateView,
    RemoveAvatarView
)

app_name = 'accounts'

urlpatterns = [
    # Registro
    path('registro/', RegistrationView.as_view(), name='register'),
    path('registro/', RegistrationView.as_view(), name='registration'),  # Alias para testes
    path('verificacao/', VerificationView.as_view(), name='verification'),

    # Autenticação
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Redefinição de senha
    path('redefinir-senha/', PasswordResetRequestView.as_view(), name='password_reset'),
    path(
        'confirmar-senha/',
        PasswordResetConfirmView.as_view(),
        name='password_reset_confirm'
    ),

    # Perfil
    path('perfil/', UserProfileView.as_view(), name='profile'),
    path('perfil/<slug:slug>/', UserProfileView.as_view(), name='profile_with_slug'),
    path('configuracoes/', UserUpdateView.as_view(), name='settings'),
    path('remover-avatar/', RemoveAvatarView.as_view(), name='remove_avatar'),
]