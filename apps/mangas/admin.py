from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Manga, Volume, Capitulo, Pagina

@admin.register(Manga)
class MangaAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'is_published', 'view_count', 'created_at')
    list_filter = ('is_published', 'created_at', 'updated_at')
    search_fields = ('title', 'author', 'description')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at', 'view_count', 'cover_preview')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('title', 'slug', 'author', 'description')
        }),
        ('Publicação', {
            'fields': ('is_published', 'criado_por')
        }),
        ('Imagem', {
            'fields': ('cover_image', 'cover_preview')
        }),
        ('Estatísticas', {
            'fields': ('view_count',),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def cover_preview(self, obj):
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="max-height: 200px; max-width: 200px;" />',
                obj.cover_image.url
            )
        return "Sem capa"
    cover_preview.short_description = "Preview da Capa"

@admin.register(Volume)
class VolumeAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'number', 'title', 'manga', 'is_published', 'extracted')
    list_filter = ('is_published', 'extracted', 'created_at')
    search_fields = ('title', 'manga__title')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at', 'cover_preview')
    raw_id_fields = ('manga',)
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('manga', 'number', 'title', 'slug')
        }),
        ('Publicação', {
            'fields': ('is_published', 'extracted')
        }),
        ('Imagem', {
            'fields': ('cover_image', 'cover_preview')
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def cover_preview(self, obj):
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="max-height: 150px; max-width: 150px;" />',
                obj.cover_image.url
            )
        return "Sem capa"
    cover_preview.short_description = "Preview da Capa"

@admin.register(Capitulo)
class CapituloAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'number', 'title', 'volume', 'views', 'is_published')
    list_filter = ('is_published', 'created_at')
    search_fields = ('title', 'volume__title', 'volume__manga__title')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('views', 'created_at', 'updated_at')
    raw_id_fields = ('volume',)
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('volume', 'number', 'title', 'slug')
        }),
        ('Publicação', {
            'fields': ('is_published',)
        }),
        ('Estatísticas', {
            'fields': ('views',),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(Pagina)
class PaginaAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'number', 'capitulo', 'image_preview', 'file_size')
    list_filter = ('created_at', 'content_type')
    search_fields = ('capitulo__title', 'capitulo__volume__title', 'capitulo__volume__manga__title')
    readonly_fields = ('width', 'height', 'file_size', 'content_type', 'created_at', 'updated_at', 'image_preview')
    raw_id_fields = ('capitulo',)
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('capitulo', 'number', 'image')
        }),
        ('Propriedades da Imagem', {
            'fields': ('image_preview', 'width', 'height', 'file_size', 'content_type'),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.image.url
            )
        return "Sem imagem"
    image_preview.short_description = "Preview da Imagem"
