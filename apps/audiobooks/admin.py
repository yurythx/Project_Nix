from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.audiobooks.models import VideoAudio, VideoProgress, VideoFavorite


class VideoProgressInline(admin.TabularInline):
    model = VideoProgress
    extra = 0
    readonly_fields = ('user', 'current_time', 'is_completed', 'last_played')
    can_delete = False
    max_num = 0
    show_change_link = True
    
    def has_add_permission(self, request, obj=None):
        return False


class VideoFavoriteInline(admin.TabularInline):
    model = VideoFavorite
    extra = 0
    readonly_fields = ('user', 'created_at')
    can_delete = True
    show_change_link = True


@admin.register(VideoAudio)
class VideoAudioAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'duration_display', 'is_public', 'is_featured', 'created_at')
    list_filter = ('category', 'is_public', 'is_featured', 'created_at')
    search_fields = ('title', 'author', 'narrator', 'description')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at', 'duration_display', 'video_preview')
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'description', 'category')
        }),
        (_('Informações do Autor/Narrador'), {
            'fields': ('author', 'narrator')
        }),
        (_('Mídia'), {
            'fields': ('thumbnail', 'thumbnail_preview', 'video_file', 'external_url')
        }),
        (_('Metadados'), {
            'fields': ('duration', 'published_date', 'is_featured', 'is_public')
        }),
        (_('Datas'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [VideoProgressInline, VideoFavoriteInline]
    
    def duration_display(self, obj):
        return obj.get_duration_display() if obj.duration else '--:--'
    duration_display.short_description = _('Duração')
    
    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" style="max-height: 100px;" />', obj.thumbnail.url)
        return 'Sem thumbnail'
    thumbnail_preview.short_description = _('Prévia da Thumbnail')
    
    def video_preview(self, obj):
        if obj.video_file:
            return format_html(
                '<video width="320" height="240" controls style="max-width: 100%;">'
                '<source src="{}" type="video/mp4">'
                'Seu navegador não suporta a tag de vídeo.'
                '</video>',
                obj.video_file.url
            )
        elif obj.external_url:
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                obj.external_url,
                obj.external_url
            )
        return 'Nenhuma mídia disponível'
    video_preview.short_description = _('Prévia do Vídeo')


@admin.register(VideoProgress)
class VideoProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'video', 'progress_percentage', 'is_completed', 'last_played')
    list_filter = ('is_completed', 'last_played')
    search_fields = ('user__username', 'video__title')
    readonly_fields = ('user', 'video', 'current_time', 'is_completed', 'last_played', 'progress_percentage')
    
    def progress_percentage(self, obj):
        if obj.video.duration:
            percentage = (obj.current_time / obj.video.duration.total_seconds()) * 100
            return f"{percentage:.1f}%"
        return '--'
    progress_percentage.short_description = _('Progresso')


@admin.register(VideoFavorite)
class VideoFavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'video', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'video__title')
    readonly_fields = ('user', 'video', 'created_at')
