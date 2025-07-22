from django.contrib import admin
from django.utils.html import format_html
from apps.pages.models import Page, NavigationItem, SEOSettings

@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    """Admin para páginas"""
    list_display = ['title', 'slug', 'status', 'is_homepage', 'show_in_menu', 'view_count', 'created_at']
    list_filter = ['status', 'is_homepage', 'show_in_menu', 'template', 'created_at']
    search_fields = ['title', 'content', 'meta_keywords']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['view_count', 'created_at', 'updated_at']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('title', 'slug', 'content', 'excerpt', 'status')
        }),
        ('Configurações', {
            'fields': ('template', 'is_homepage', 'show_in_menu', 'menu_order', 'parent')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('Auditoria', {
            'fields': ('created_by', 'updated_by', 'view_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # Criando novo
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(NavigationItem)
class NavigationItemAdmin(admin.ModelAdmin):
    """Admin para itens de navegação"""
    list_display = ['title', 'nav_type', 'order', 'is_active', 'parent']
    list_filter = ['nav_type', 'is_active']
    search_fields = ['title', 'url']
    ordering = ['order', 'title']

@admin.register(SEOSettings)
class SEOSettingsAdmin(admin.ModelAdmin):
    """Admin para configurações de SEO"""
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('site_name', 'site_description', 'site_keywords')
        }),
        ('Imagens', {
            'fields': ('default_og_image', 'favicon')
        }),
        ('Analytics', {
            'fields': ('google_analytics_id', 'google_tag_manager_id', 'facebook_pixel_id')
        }),
        ('Redes Sociais', {
            'fields': ('facebook_url', 'twitter_url', 'instagram_url', 'linkedin_url', 'youtube_url')
        }),
        ('Contato', {
            'fields': ('contact_email', 'contact_phone', 'address')
        }),
        ('Configurações Técnicas', {
            'fields': ('organization_type', 'robots_txt', 'enable_sitemap'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        # Permite apenas uma instância
        return not SEOSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Não permite deletar configurações
        return False
