from django.db import models
from django.core.validators import MinLengthValidator, MaxLengthValidator

class SEOSettings(models.Model):
    """Modelo para configurações globais de SEO"""
    
    site_name = models.CharField(
        'nome do site',
        max_length=100,
        help_text='Nome do site para SEO'
    )
    site_description = models.TextField(
        'descrição do site',
        max_length=160,
        validators=[MaxLengthValidator(160)],
        help_text='Descrição geral do site (máximo 160 caracteres)'
    )
    site_keywords = models.TextField(
        'palavras-chave do site',
        max_length=255,
        blank=True,
        help_text='Palavras-chave gerais separadas por vírgula'
    )
    default_og_image = models.ImageField(
        'imagem padrão Open Graph',
        upload_to='seo/og_images/',
        blank=True,
        help_text='Imagem padrão para compartilhamento em redes sociais'
    )
    favicon = models.ImageField(
        'favicon',
        upload_to='seo/favicons/',
        blank=True,
        help_text='Ícone do site (favicon)'
    )
    
    # Analytics
    google_analytics_id = models.CharField(
        'Google Analytics ID',
        max_length=20,
        blank=True,
        help_text='ID do Google Analytics (ex: GA_MEASUREMENT_ID)'
    )
    google_tag_manager_id = models.CharField(
        'Google Tag Manager ID',
        max_length=20,
        blank=True,
        help_text='ID do Google Tag Manager (ex: GTM-XXXXXXX)'
    )
    facebook_pixel_id = models.CharField(
        'Facebook Pixel ID',
        max_length=20,
        blank=True,
        help_text='ID do Facebook Pixel'
    )
    
    # Social Media
    facebook_url = models.URLField(
        'URL do Facebook',
        blank=True,
        help_text='URL da página do Facebook'
    )
    twitter_url = models.URLField(
        'URL do Twitter',
        blank=True,
        help_text='URL do perfil do Twitter'
    )
    instagram_url = models.URLField(
        'URL do Instagram',
        blank=True,
        help_text='URL do perfil do Instagram'
    )
    linkedin_url = models.URLField(
        'URL do LinkedIn',
        blank=True,
        help_text='URL do perfil do LinkedIn'
    )
    youtube_url = models.URLField(
        'URL do YouTube',
        blank=True,
        help_text='URL do canal do YouTube'
    )
    
    # Contact Info
    contact_email = models.EmailField(
        'email de contato',
        blank=True,
        help_text='Email principal de contato'
    )
    contact_phone = models.CharField(
        'telefone de contato',
        max_length=20,
        blank=True,
        help_text='Telefone principal de contato'
    )
    address = models.TextField(
        'endereço',
        blank=True,
        help_text='Endereço físico da empresa'
    )
    
    # Schema.org
    organization_type = models.CharField(
        'tipo de organização',
        max_length=50,
        default='Organization',
        help_text='Tipo de organização para Schema.org'
    )
    
    # Robots and Sitemap
    robots_txt = models.TextField(
        'robots.txt',
        blank=True,
        help_text='Conteúdo do arquivo robots.txt'
    )
    enable_sitemap = models.BooleanField(
        'habilitar sitemap',
        default=True,
        help_text='Se deve gerar sitemap automaticamente'
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
        verbose_name = 'configuração de SEO'
        verbose_name_plural = 'configurações de SEO'

    def __str__(self):
        return f"SEO Settings - {self.site_name}"

    def save(self, *args, **kwargs):
        """Garante que existe apenas uma instância de configurações SEO"""
        if not self.pk and SEOSettings.objects.exists():
            # Se já existe uma instância, atualiza ela em vez de criar nova
            existing = SEOSettings.objects.first()
            existing.__dict__.update(self.__dict__)
            existing.save()
            return existing
        return super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        """Retorna as configurações de SEO (singleton)"""
        settings, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'site_name': 'Havoc',
                'site_description': 'Sistema de gerenciamento de conteúdo',
                'organization_type': 'Organization'
            }
        )
        return settings

    def get_social_links(self):
        """Retorna links de redes sociais ativos"""
        links = []
        social_fields = [
            ('facebook_url', 'Facebook', 'fab fa-facebook'),
            ('twitter_url', 'Twitter', 'fab fa-twitter'),
            ('instagram_url', 'Instagram', 'fab fa-instagram'),
            ('linkedin_url', 'LinkedIn', 'fab fa-linkedin'),
            ('youtube_url', 'YouTube', 'fab fa-youtube'),
        ]
        
        for field, name, icon in social_fields:
            url = getattr(self, field)
            if url:
                links.append({
                    'name': name,
                    'url': url,
                    'icon': icon
                })
        
        return links
