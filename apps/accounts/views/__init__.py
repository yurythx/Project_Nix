from .registration import RegistrationView, VerificationView
from .authentication import LoginView, LogoutView
from .password_reset import PasswordResetRequestView, PasswordResetConfirmView
from .profile import UserProfileView, UserUpdateView, RemoveAvatarView

__all__ = [
    'RegistrationView',
    'VerificationView',
    'LoginView',
    'LogoutView',
    'PasswordResetRequestView',
    'PasswordResetConfirmView',
    'UserProfileView',
    'UserUpdateView',
    'RemoveAvatarView',
]