from django.db import models
from django.core.validators import URLValidator

class NavigationItem(models.Model):
    """Modelo para itens de navegação personalizados"""
    
    TYPE_CHOICES = [
        ('page', 'Página'),
        ('url', 'URL Externa'),
        ('category', 'Categoria'),
    ]
    
    title = models.CharField(
        'título',
        max_length=100,
        help_text='Texto exibido no menu'
    )
    url = models.CharField(
        'URL',
        max_length=255,
        blank=True,
        help_text='URL personalizada (para links externos)'
    )
    page = models.ForeignKey(
        'pages.Page',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='página',
        help_text='Página interna do site'
    )
    nav_type = models.CharField(
        'tipo',
        max_length=20,
        choices=TYPE_CHOICES,
        default='page',
        help_text='Tipo de item de navegação'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='item pai',
        help_text='Item pai para criar submenus'
    )
    order = models.PositiveIntegerField(
        'ordem',
        default=0,
        help_text='Ordem de exibição no menu'
    )
    is_active = models.BooleanField(
        'ativo',
        default=True,
        help_text='Se o item deve ser exibido no menu'
    )
    open_in_new_tab = models.BooleanField(
        'abrir em nova aba',
        default=False,
        help_text='Se o link deve abrir em nova aba'
    )
    css_class = models.CharField(
        'classe CSS',
        max_length=100,
        blank=True,
        help_text='Classes CSS personalizadas para o item'
    )
    icon = models.CharField(
        'ícone',
        max_length=50,
        blank=True,
        help_text='Classe do ícone (ex: fas fa-home)'
    )
    created_at = models.DateTimeField(
        'criado em',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        'atualizado em',
        auto_now=True
    )

    class Meta:
        verbose_name = 'item de navegação'
        verbose_name_plural = 'itens de navegação'
        ordering = ['order', 'title']

    def __str__(self):
        return self.title

    def clean(self):
        """Validações customizadas"""
        from django.core.exceptions import ValidationError
        
        if self.nav_type == 'page' and not self.page:
            raise ValidationError('Página é obrigatória para itens do tipo "Página"')
        
        if self.nav_type == 'url' and not self.url:
            raise ValidationError('URL é obrigatória para itens do tipo "URL Externa"')
        
        if self.url:
            validator = URLValidator()
            try:
                validator(self.url)
            except ValidationError:
                raise ValidationError('URL inválida')

    def get_url(self):
        """Retorna a URL do item de navegação"""
        if self.nav_type == 'page' and self.page:
            return self.page.get_absolute_url()
        elif self.nav_type == 'url' and self.url:
            return self.url
        return '#'

    def get_children(self):
        """Retorna itens filhos"""
        return self.navigationitem_set.filter(is_active=True).order_by('order', 'title')

    @property
    def has_children(self):
        """Verifica se tem itens filhos"""
        return self.get_children().exists()
