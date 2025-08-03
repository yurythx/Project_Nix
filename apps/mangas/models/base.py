from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

class SlugMixin:
    """Mixin para gerenciamento de slugs únicos"""
    
    def generate_unique_slug(self, text, max_length=50, field_name='slug'):
        """
        Gera um slug único baseado no texto fornecido.
        Se já existir um slug igual, adiciona um número sequencial (001, 002, etc.)
        
        Args:
            text: Texto para gerar o slug
            max_length: Tamanho máximo do slug
            field_name: Nome do campo slug no modelo
            
        Returns:
            str: Slug único no formato 'texto' ou 'texto-001', 'texto-002', etc.
        """
        # Verifica se o texto está vazio
        if not text or not text.strip():
            text = 'untitled'
            
        # Gera o slug base - garantindo que não exceda o tamanho máximo
        # Reserva espaço para o sufixo numérico (-001, -002, etc.)
        reserved_suffix_length = 5  # -XXX formato
        effective_max_length = max(max_length - reserved_suffix_length, 10)
        
        # Gera o slug base e remove traços no final
        base_slug = slugify(text)[:effective_max_length].strip('-')
        
        # Se o slug base estiver vazio após slugify (caracteres especiais), usa 'untitled'
        if not base_slug:
            base_slug = 'untitled'
            
        unique_slug = base_slug
        
        # Verifica se já existe um objeto com este slug
        model = self.__class__
        num = 1
        
        # Tenta até 1000 vezes para evitar loop infinito
        max_attempts = 1000
        attempt = 0
        
        while attempt < max_attempts and model.objects.filter(**{field_name: unique_slug}).exclude(pk=getattr(self, 'pk', None)).exists():
            # Adiciona um número formatado com 3 dígitos (001, 002, etc.)
            unique_slug = f"{base_slug}-{num:03d}"
            num += 1
            attempt += 1
            
            # Se o slug ficar maior que o tamanho máximo, trunca o base_slug
            if len(unique_slug) > max_length:
                # Reduz o tamanho do base_slug para acomodar o sufixo
                base_slug = base_slug[:max_length - reserved_suffix_length]
                unique_slug = f"{base_slug}-{num:03d}"
        
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
