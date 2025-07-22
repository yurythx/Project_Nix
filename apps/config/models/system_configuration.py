from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator
import json

User = get_user_model()

class SystemConfiguration(models.Model):
    """Modelo para configurações do sistema"""
    
    key = models.CharField(
        'chave',
        max_length=100,
        unique=True,
        validators=[MinLengthValidator(3)],
        help_text='Chave única da configuração'
    )
    value = models.TextField(
        'valor',
        help_text='Valor da configuração (pode ser JSON)'
    )
    description = models.TextField(
        'descrição',
        blank=True,
        help_text='Descrição da configuração'
    )
    is_active = models.BooleanField(
        'ativo',
        default=True,
        help_text='Se a configuração está ativa'
    )
    created_at = models.DateTimeField(
        'criado em',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        'atualizado em',
        auto_now=True
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='atualizado por',
        help_text='Usuário que fez a última atualização'
    )

    class Meta:
        verbose_name = 'configuração do sistema'
        verbose_name_plural = 'configurações do sistema'
        ordering = ['key']

    def __str__(self):
        return f"{self.key}: {self.value[:50]}..."

    def get_value_as_json(self):
        """Retorna o valor como JSON se possível"""
        try:
            return json.loads(self.value)
        except (json.JSONDecodeError, TypeError):
            return self.value

    def set_value_from_dict(self, data):
        """Define o valor a partir de um dicionário"""
        self.value = json.dumps(data, ensure_ascii=False, indent=2)
