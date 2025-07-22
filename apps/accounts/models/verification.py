from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

User = get_user_model()

class VerificationCode(models.Model):
    """Modelo para armazenar códigos de verificação de usuários"""
    
    REGISTRATION = 'registration'
    PASSWORD_RESET = 'password_reset'
    EMAIL_CHANGE = 'email_change'
    
    CODE_TYPES = [
        (REGISTRATION, 'Registro de Conta'),
        (PASSWORD_RESET, 'Redefinição de Senha'),
        (EMAIL_CHANGE, 'Alteração de Email'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='usuário',
        related_name='verification_codes'
    )
    code = models.CharField(
        'código',
        max_length=6,
        help_text='Código de 6 dígitos para verificação'
    )
    code_type = models.CharField(
        'tipo de código',
        max_length=20,
        choices=CODE_TYPES,
        help_text='Tipo de verificação que o código será usado'
    )
    created_at = models.DateTimeField(
        'criado em',
        auto_now_add=True
    )
    expires_at = models.DateTimeField(
        'expira em',
        help_text='Data e hora em que o código expira'
    )
    
    class Meta:
        verbose_name = 'código de verificação'
        verbose_name_plural = 'códigos de verificação'
        unique_together = ('user', 'code_type')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.get_code_type_display()} - {self.code}"
    
    def is_expired(self):
        """Verifica se o código expirou"""
        return timezone.now() > self.expires_at
    
    def save(self, *args, **kwargs):
        """Define a data de expiração ao criar o código"""
        if not self.pk:
            self.expires_at = timezone.now() + timedelta(minutes=15)
        super().save(*args, **kwargs)