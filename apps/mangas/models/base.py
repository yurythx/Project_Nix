from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

class SlugMixin:
    """Mixin para gerenciamento de slugs únicos"""
    
    def generate_unique_slug(self, text, max_length=50, field_name='slug'):
        """
        Gera um slug único baseado no texto fornecido.
        
        Args:
            text: Texto para gerar o slug
            max_length: Tamanho máximo do slug
            field_name: Nome do campo slug no modelo
            
        Returns:
            str: Slug único
        """
        # Gera o slug base
        slug = slugify(text)[:max_length].strip('-')
        unique_slug = slug
        
        # Verifica se já existe um objeto com este slug
        model = self.__class__
        num = 1
        
        while model.objects.filter(**{field_name: unique_slug}).exclude(pk=self.pk).exists():
            # Adiciona um número ao final do slug para torná-lo único
            unique_slug = f"{slug}-{num}"
            num += 1
            
        return unique_slug

class TimestampMixin(models.Model):
    """Mixin para adicionar campos de data de criação e atualização"""
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)
    
    class Meta:
        abstract = True

class SoftDeleteMixin(models.Model):
    """Mixin para exclusão lógica"""
    is_deleted = models.BooleanField(_('Excluído?'), default=False, db_index=True)
    deleted_at = models.DateTimeField(_('Excluído em'), null=True, blank=True)
    
    class Meta:
        abstract = True
        
    def delete(self, *args, **kwargs):
        """Sobrescreve o método delete para fazer exclusão lógica"""
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])
        
    def hard_delete(self, *args, **kwargs):
        """Remove o registro permanentemente do banco de dados"""
        super().delete(*args, **kwargs)
