from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.text import slugify
from django.urls import reverse
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
import os
from PIL import Image

class UserManager(BaseUserManager):
    """Gerenciador personalizado para o modelo User com email como nome de usuário"""
    
    def create_user(self, email, password=None, **extra_fields):
        """Cria e salva um usuário com email e senha"""
        if not email:
            raise ValueError('O email é obrigatório')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Cria e salva um superusuário com email e senha"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser deve ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser deve ter is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

def user_avatar_path(instance, filename):
    """Gera o caminho para upload do avatar do usuário"""
    # Pega a extensão do arquivo
    ext = filename.split('.')[-1]
    # Gera nome único baseado no ID do usuário
    filename = f'avatar_{instance.id}.{ext}'
    return f'avatars/{filename}'

class User(AbstractUser):
    """Modelo de usuário personalizado usando email como identificador principal"""
    
    email = models.EmailField(
        'endereço de email',
        unique=True,
        error_messages={
            'unique': "Já existe um usuário com este email.",
        }
    )
    is_verified = models.BooleanField(
        'verificado',
        default=False,
        help_text='Designa se o usuário verificou o email.'
    )
    slug = models.SlugField(
        'slug',
        max_length=100,
        unique=True,
        blank=True,
        help_text='Identificador único para URLs amigáveis'
    )
    avatar = models.ImageField(
        'avatar',
        upload_to=user_avatar_path,
        blank=True,
        null=True,
        help_text='Foto de perfil do usuário'
    )
    bio = models.TextField(
        'biografia',
        max_length=500,
        blank=True,
        help_text='Breve descrição sobre o usuário'
    )
    phone = models.CharField(
        'telefone',
        max_length=20,
        blank=True,
        help_text='Número de telefone do usuário'
    )
    birth_date = models.DateField(
        'data de nascimento',
        blank=True,
        null=True,
        help_text='Data de nascimento do usuário'
    )
    location = models.CharField(
        'localização',
        max_length=100,
        blank=True,
        help_text='Cidade/Estado do usuário'
    )
    
    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'usuário'
        verbose_name_plural = 'usuários'
        ordering = ['-date_joined']

    def __str__(self):
        return self.email

    def get_absolute_url(self):
        """Retorna a URL para acessar a página de perfil do usuário"""
        return reverse('accounts:profile_with_slug', kwargs={'slug': self.slug})

    def get_full_name(self):
        """Retorna o nome completo do usuário"""
        return f"{self.first_name} {self.last_name}".strip()

    def generate_slug(self):
        """Gera um slug único baseado no email"""
        base_slug = slugify(self.email.split('@')[0])
        unique_slug = base_slug
        num = 1
        while User.objects.filter(slug=unique_slug).exists():
            unique_slug = f"{base_slug}-{num}"
            num += 1
        return unique_slug

    def get_avatar_url(self):
        """Retorna a URL do avatar ou um avatar padrão"""
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        return self.get_default_avatar()

    def get_default_avatar(self):
        """Retorna um avatar padrão baseado nas iniciais do usuário"""
        initials = self.get_initials()
        # Usando um serviço de avatar baseado em iniciais
        return f"https://ui-avatars.com/api/?name={initials}&size=200&background=007bff&color=fff&bold=true"

    def get_initials(self):
        """Retorna as iniciais do usuário"""
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        elif self.first_name:
            return self.first_name[0].upper()
        elif self.last_name:
            return self.last_name[0].upper()
        else:
            return self.email[0].upper()

    def save(self, *args, **kwargs):
        """Override do save para redimensionar avatar"""
        super().save(*args, **kwargs)

        # Redimensiona o avatar se necessário
        if self.avatar:
            self.resize_avatar()

    def resize_avatar(self):
        """Redimensiona o avatar para 300x300 pixels"""
        try:
            img = Image.open(self.avatar.path)
            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.avatar.path)
        except Exception:
            # Se houver erro no redimensionamento, ignora
            pass

@receiver(pre_save, sender=User)
def user_pre_save(sender, instance, **kwargs):
    """Signal para gerar slug automaticamente antes de salvar"""
    if not instance.slug:
        instance.slug = instance.generate_slug()

@receiver(post_delete, sender=User)
def delete_user_avatar(sender, instance, **kwargs):
    """Signal para deletar o arquivo de avatar quando o usuário for deletado"""
    if instance.avatar:
        if os.path.isfile(instance.avatar.path):
            os.remove(instance.avatar.path)