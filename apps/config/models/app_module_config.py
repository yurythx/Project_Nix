from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator
from django.core.exceptions import ValidationError
import json
import os
from django.db.models.signals import post_migrate
from django.dispatch import receiver

User = get_user_model()


class AppModuleConfiguration(models.Model):
    """Modelo para configuração de módulos/apps do sistema"""
    
    # Apps principais obrigatórios (nunca podem ser desabilitados)
    CORE_APPS = ['accounts', 'config', 'pages']
    
    # Status do módulo
    STATUS_CHOICES = [
        ('active', 'Ativo'),
        ('inactive', 'Inativo'),
        ('maintenance', 'Manutenção'),
        ('deprecated', 'Descontinuado'),
    ]
    
    # Tipos de módulo
    MODULE_TYPE_CHOICES = [
        ('core', 'Módulo Principal'),
        ('feature', 'Funcionalidade'),
        ('integration', 'Integração'),
        ('custom', 'Personalizado'),
    ]
    
    app_name = models.CharField(
        'nome do app',
        max_length=100,
        unique=True,
        validators=[MinLengthValidator(3)],
        help_text='Nome do app Django (ex: articles, blog, shop)'
    )
    
    display_name = models.CharField(
        'nome de exibição',
        max_length=200,
        help_text='Nome amigável para exibição na interface'
    )
    
    description = models.TextField(
        'descrição',
        blank=True,
        help_text='Descrição detalhada do módulo'
    )
    
    module_type = models.CharField(
        'tipo do módulo',
        max_length=20,
        choices=MODULE_TYPE_CHOICES,
        default='feature',
        help_text='Tipo/categoria do módulo'
    )
    
    status = models.CharField(
        'status',
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        help_text='Status atual do módulo'
    )
    
    is_enabled = models.BooleanField(
        'habilitado',
        default=True,
        help_text='Se o módulo está habilitado no sistema'
    )
    
    is_core = models.BooleanField(
        'módulo principal',
        default=False,
        help_text='Se é um módulo principal (não pode ser desabilitado)'
    )
    
    # URLs e navegação
    url_pattern = models.CharField(
        'padrão de URL',
        max_length=200,
        blank=True,
        help_text='Padrão de URL do módulo (ex: artigos/, blog/)'
    )
    
    menu_icon = models.CharField(
        'ícone do menu',
        max_length=100,
        blank=True,
        default='fas fa-puzzle-piece',
        help_text='Classe do ícone FontAwesome para o menu'
    )
    
    menu_order = models.PositiveIntegerField(
        'ordem no menu',
        default=100,
        help_text='Ordem de exibição no menu (menor = primeiro)'
    )
    
    show_in_menu = models.BooleanField(
        'exibir no menu',
        default=True,
        help_text='Se deve aparecer no menu de navegação'
    )
    
    # Dependências e requisitos
    dependencies = models.JSONField(
        'dependências',
        default=list,
        blank=True,
        help_text='Lista de apps que este módulo depende'
    )
    
    required_permissions = models.JSONField(
        'permissões necessárias',
        default=list,
        blank=True,
        help_text='Lista de permissões necessárias para usar o módulo'
    )
    
    # Configurações específicas do módulo
    module_settings = models.JSONField(
        'configurações do módulo',
        default=dict,
        blank=True,
        help_text='Configurações específicas do módulo em formato JSON'
    )
    
    # Metadados
    version = models.CharField(
        'versão',
        max_length=20,
        blank=True,
        help_text='Versão do módulo'
    )
    
    author = models.CharField(
        'autor',
        max_length=200,
        blank=True,
        help_text='Autor/desenvolvedor do módulo'
    )
    
    documentation_url = models.URLField(
        'URL da documentação',
        blank=True,
        help_text='Link para documentação do módulo'
    )
    
    # Controle de acesso
    created_at = models.DateTimeField(
        'criado em',
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        'atualizado em',
        auto_now=True
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='modules_created',
        verbose_name='criado por'
    )
    
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='modules_updated',
        verbose_name='atualizado por'
    )
    
    class Meta:
        verbose_name = 'configuração de módulo'
        verbose_name_plural = 'configurações de módulos'
        ordering = ['menu_order', 'display_name']
        indexes = [
            models.Index(fields=['app_name']),
            models.Index(fields=['is_enabled', 'status']),
            models.Index(fields=['module_type']),
        ]
    
    def __str__(self):
        return f"{self.display_name} ({self.app_name})"
    
    def clean(self):
        """Validações customizadas"""
        super().clean()
        
        # Apps principais não podem ser desabilitados
        if self.app_name in self.CORE_APPS:
            self.is_core = True
            if not self.is_enabled:
                raise ValidationError(
                    f'O módulo {self.app_name} é principal e não pode ser desabilitado.'
                )
        
        # Validar dependências
        if self.dependencies:
            for dep in self.dependencies:
                if not isinstance(dep, str):
                    raise ValidationError('Dependências devem ser uma lista de strings.')
    
    def save(self, *args, **kwargs):
        """Override do save para aplicar regras de negócio"""
        self.clean()
        
        # Define automaticamente como core se for um app principal
        if self.app_name in self.CORE_APPS:
            self.is_core = True
            self.is_enabled = True
            self.module_type = 'core'
        
        super().save(*args, **kwargs)
    
    @property
    def is_available(self):
        """Verifica se o módulo está disponível para uso"""
        return self.is_enabled and self.status == 'active'
    
    @property
    def can_be_disabled(self):
        """Verifica se o módulo pode ser desabilitado"""
        return not self.is_core
    
    def get_menu_icon_html(self):
        """Retorna o HTML do ícone para o menu"""
        return f'<i class="{self.menu_icon}"></i>'
    
    def check_dependencies(self):
        """Verifica se todas as dependências estão ativas"""
        if not self.dependencies:
            return True
        
        for dep_name in self.dependencies:
            try:
                dep = AppModuleConfiguration.objects.get(app_name=dep_name)
                if not dep.is_available:
                    return False
            except AppModuleConfiguration.DoesNotExist:
                return False
        
        return True
    
    def get_dependent_modules(self):
        """Retorna módulos que dependem deste"""
        # Busca todos os módulos habilitados e filtra manualmente
        # para compatibilidade com SQLite
        dependent_modules = []
        for module in AppModuleConfiguration.objects.filter(is_enabled=True):
            if module.dependencies and self.app_name in module.dependencies:
                dependent_modules.append(module)

        # Retorna um QuerySet-like object
        return AppModuleConfiguration.objects.filter(
            id__in=[m.id for m in dependent_modules]
        )
    
    @classmethod
    def get_enabled_modules(cls):
        """Retorna todos os módulos habilitados"""
        return cls.objects.filter(is_enabled=True, status='active')
    
    @classmethod
    def get_core_modules(cls):
        """Retorna módulos principais"""
        return cls.objects.filter(is_core=True)
    
    @classmethod
    def initialize_core_modules(cls):
        """Inicializa os módulos principais se não existirem e adiciona exemplos em dev/teste"""
        core_modules_data = [
            {
                'app_name': 'accounts',
                'display_name': 'Contas e Usuários',
                'description': 'Sistema de autenticação, registro e gerenciamento de usuários',
                'url_pattern': 'accounts/',
                'menu_icon': 'fas fa-users',
                'menu_order': 10,
            },
            {
                'app_name': 'config',
                'display_name': 'Configurações',
                'description': 'Painel de configurações e administração do sistema',
                'url_pattern': 'config/',
                'menu_icon': 'fas fa-cogs',
                'menu_order': 90,
            },
            {
                'app_name': 'pages',
                'display_name': 'Páginas',
                'description': 'Sistema de páginas estáticas e dinâmicas',
                'url_pattern': '',
                'menu_icon': 'fas fa-file-alt',
                'menu_order': 20,
            },
        ]
        for module_data in core_modules_data:
            cls.objects.get_or_create(
                app_name=module_data['app_name'],
                defaults={
                    **module_data,
                    'module_type': 'core',
                    'is_core': True,
                    'is_enabled': True,
                    'status': 'active',
                }
            )
        # Adicionar módulos de exemplo apenas em dev/teste
        env = os.environ.get('ENVIRONMENT', '').lower()
        if env in ('development', 'dev', 'testing', 'test', ''):
            example_modules = [
                {
                    'app_name': 'blog',
                    'display_name': 'Blog',
                    'description': 'Módulo de blog com posts e comentários',
                    'url_pattern': 'blog/',
                    'menu_icon': 'fas fa-blog',
                    'menu_order': 30,
                    'module_type': 'feature',
                },
                {
                    'app_name': 'forum',
                    'display_name': 'Fórum',
                    'description': 'Módulo de fórum para discussões',
                    'url_pattern': 'forum/',
                    'menu_icon': 'fas fa-comments',
                    'menu_order': 40,
                    'module_type': 'feature',
                },
                {
                    'app_name': 'shop',
                    'display_name': 'Loja',
                    'description': 'Módulo de e-commerce',
                    'url_pattern': 'shop/',
                    'menu_icon': 'fas fa-shopping-cart',
                    'menu_order': 50,
                    'module_type': 'custom',
                },
                {
                    'app_name': 'faq',
                    'display_name': 'FAQ',
                    'description': 'Perguntas frequentes',
                    'url_pattern': 'faq/',
                    'menu_icon': 'fas fa-question-circle',
                    'menu_order': 60,
                    'module_type': 'custom',
                },
            ]
            for module_data in example_modules:
                cls.objects.get_or_create(
                    app_name=module_data['app_name'],
                    defaults={
                        **module_data,
                        'is_core': False,
                        'is_enabled': True,
                        'status': 'active',
                    }
                )

@receiver(post_migrate)
def ensure_core_modules(sender, **kwargs):
    """Garante que os módulos principais e todos os apps locais estejam sempre inicializados após migrações."""
    from apps.config.models.app_module_config import AppModuleConfiguration
    from apps.config.services.module_service import ModuleService
    AppModuleConfiguration.initialize_core_modules()
    ModuleService().sync_with_installed_apps()
