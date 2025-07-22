from django.db import models
from django.utils.text import slugify
from django.db.models.signals import pre_save
from django.dispatch import receiver

class Group(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(
        max_length=100,
        unique=True,
        blank=True,
        help_text='Identificador único para URLs amigáveis'
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def generate_slug(self):
        """Gera um slug único baseado no nome"""
        base_slug = slugify(self.name)
        unique_slug = base_slug
        num = 1
        while Group.objects.filter(slug=unique_slug).exclude(pk=self.pk).exists():
            unique_slug = f"{base_slug}-{num}"
            num += 1
        return unique_slug

@receiver(pre_save, sender=Group)
def group_pre_save(sender, instance, **kwargs):
    """Signal para gerar slug automaticamente antes de salvar"""
    if not instance.slug:
        instance.slug = instance.generate_slug() 