from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count
from django.utils import timezone
from django.contrib.admin import SimpleListFilter

from .models import Comment, CommentLike, ModerationQueue, CommentModeration, CommentNotification


class ModerationStatusFilter(SimpleListFilter):
    """Filtro personalizado para status de moderação"""
    title = 'Status de Moderação'
    parameter_name = 'moderation_status'

    def lookups(self, request, model_admin):
        return (
            ('approved', 'Aprovado'),
            ('pending', 'Pendente'),
            ('rejected', 'Rejeitado'),
            ('spam', 'Spam'),
            ('deleted', 'Deletado'),
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


class HasRepliesFilter(SimpleListFilter):
    """Filtro para comentários com respostas"""
    title = 'Tem Respostas'
    parameter_name = 'has_replies'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Sim'),
            ('no', 'Não'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(replies_count__gt=0)
        elif self.value() == 'no':
            return queryset.filter(replies_count=0)
        return queryset


class CommentLikeInline(admin.TabularInline):
    """Inline para reações de comentários"""
    model = CommentLike
    extra = 0
    readonly_fields = ('user', 'reaction', 'created_at')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin para comentários"""
    list_display = [
        'content_preview', 'author_info', 'content_object_link',
        'status_display', 'replies_info', 'reactions_info',
        'created_at', 'actions_display'
    ]
    list_filter = [
        ModerationStatusFilter, HasRepliesFilter, 'is_pinned',
        'created_at', 'updated_at',
        ('author', admin.RelatedOnlyFieldListFilter),
        ('content_type', admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = [
        'content', 'author__username', 'author__email',
        'uuid', 'ip_address'
    ]
    readonly_fields = [
        'uuid', 'created_at', 'updated_at', 'ip_address',
        'user_agent', 'replies_count', 'likes_count',
        'dislikes_count', 'content_type', 'object_id'
    ]
    raw_id_fields = ['author', 'parent', 'moderated_by']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    list_per_page = 25
    inlines = [CommentLikeInline]

    fieldsets = (
        ('Informações do Comentário', {
            'fields': ('uuid', 'content', 'author', 'parent')
        }),
        ('Objeto Relacionado', {
            'fields': ('content_type', 'object_id'),
            'classes': ('collapse',)
        }),
        ('Moderação', {
            'fields': ('status', 'moderated_by', 'moderation_reason', 'is_pinned')
        }),
        ('Estatísticas', {
            'fields': ('likes_count', 'dislikes_count', 'replies_count', 'depth'),
            'classes': ('collapse',)
        }),
        ('Flags', {
            'fields': ('is_edited',),
            'classes': ('collapse',)
        }),
        ('Dados Técnicos', {
            'fields': ('ip_address', 'user_agent', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = [
        'approve_comments', 'reject_comments', 'mark_as_spam',
        'pin_comments', 'unpin_comments', 'delete_selected'
    ]

    def content_preview(self, obj):
        """Preview do conteúdo do comentário"""
        content = obj.content[:100]
        if len(obj.content) > 100:
            content += '...'
        return format_html('<div style="max-width: 300px;">{}</div>', content)
    content_preview.short_description = 'Conteúdo'

    def author_info(self, obj):
        """Informações do autor"""
        if obj.author:
            admin_url = reverse('admin:auth_user_change', args=[obj.author.pk])
            return format_html(
                '<a href="{}">{}</a><br><small>{}</small>',
                admin_url, obj.author.username, obj.author.email
            )
        return '-'
    author_info.short_description = 'Autor'

    def content_object_link(self, obj):
        """Link para o objeto relacionado"""
        if obj.content_object:
            return format_html(
                '{}<br><small>ID: {}</small>',
                str(obj.content_object)[:50], obj.object_id
            )
        return '-'
    content_object_link.short_description = 'Objeto'

    def status_display(self, obj):
        """Display colorido do status"""
        colors = {
            'approved': 'green',
            'pending': 'orange',
            'rejected': 'red',
            'spam': 'darkred',
            'deleted': 'gray'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Status'

    def replies_info(self, obj):
        """Informações sobre respostas"""
        if obj.replies_count > 0:
            return format_html(
                '<strong>{}</strong> resposta{}<br><small>Profundidade: {}</small>',
                obj.replies_count,
                's' if obj.replies_count != 1 else '',
                obj.depth
            )
        return format_html('<small>Sem respostas</small>')
    replies_info.short_description = 'Respostas'

    def reactions_info(self, obj):
        """Informações sobre reações"""
        return format_html(
            '👍 {} | 👎 {}',
            obj.likes_count, obj.dislikes_count
        )
    reactions_info.short_description = 'Reações'

    def actions_display(self, obj):
        """Ações disponíveis"""
        actions = []
        
        if obj.status == 'pending':
            actions.append('✅ Aprovar')
            actions.append('❌ Rejeitar')
        
        if obj.status != 'deleted':
            actions.append('🗑️ Deletar')
        
        if not obj.is_pinned and obj.status == 'approved':
            actions.append('📌 Fixar')
        elif obj.is_pinned:
            actions.append('📌 Desfixar')
        
        return format_html('<br>'.join(actions))
    actions_display.short_description = 'Ações'

    def approve_comments(self, request, queryset):
        """Aprovar comentários selecionados"""
        updated = queryset.update(status='approved', moderated_by=request.user)
        self.message_user(
            request,
            f'{updated} comentário(s) aprovado(s) com sucesso.'
        )
    approve_comments.short_description = "✅ Aprovar comentários selecionados"

    def reject_comments(self, request, queryset):
        """Rejeitar comentários selecionados"""
        updated = queryset.update(status='rejected', moderated_by=request.user)
        self.message_user(
            request,
            f'{updated} comentário(s) rejeitado(s) com sucesso.'
        )
    reject_comments.short_description = "❌ Rejeitar comentários selecionados"

    def mark_as_spam(self, request, queryset):
        """Marcar como spam"""
        updated = queryset.update(status='spam', moderated_by=request.user)
        self.message_user(
            request,
            f'{updated} comentário(s) marcado(s) como spam.'
        )
    mark_as_spam.short_description = "🚫 Marcar como spam"

    def pin_comments(self, request, queryset):
        """Fixar comentários"""
        updated = queryset.filter(status='approved').update(is_pinned=True)
        self.message_user(
            request,
            f'{updated} comentário(s) fixado(s) com sucesso.'
        )
    pin_comments.short_description = "📌 Fixar comentários"

    def unpin_comments(self, request, queryset):
        """Desfixar comentários"""
        updated = queryset.update(is_pinned=False)
        self.message_user(
            request,
            f'{updated} comentário(s) desfixado(s) com sucesso.'
        )
    unpin_comments.short_description = "📌 Desfixar comentários"


@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    """Admin para reações de comentários"""
    list_display = ['comment_preview', 'user_info', 'reaction_display', 'created_at']
    list_filter = ['reaction', 'created_at']
    search_fields = ['comment__content', 'user__username']
    readonly_fields = ['created_at']
    raw_id_fields = ['comment', 'user']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    def comment_preview(self, obj):
        """Preview do comentário"""
        content = obj.comment.content[:50]
        if len(obj.comment.content) > 50:
            content += '...'
        return content
    comment_preview.short_description = 'Comentário'

    def user_info(self, obj):
        """Informações do usuário"""
        admin_url = reverse('admin:auth_user_change', args=[obj.user.pk])
        return format_html(
            '<a href="{}">{}</a>',
            admin_url, obj.user.username
        )
    user_info.short_description = 'Usuário'

    def reaction_display(self, obj):
        """Display da reação"""
        icons = {'like': '👍', 'dislike': '👎'}
        return format_html(
            '{} {}',
            icons.get(obj.reaction, ''),
            obj.get_reaction_display()
        )
    reaction_display.short_description = 'Reação'


@admin.register(ModerationQueue)
class ModerationQueueAdmin(admin.ModelAdmin):
    """Admin para fila de moderação"""
    list_display = [
        'comment_preview', 'priority_display',
        'assigned_to_info', 'created_at', 'actions_display'
    ]
    list_filter = ['priority', 'created_at', 'assigned_to']
    search_fields = ['comment__content', 'comment__author__username']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['comment', 'assigned_to']
    date_hierarchy = 'created_at'
    ordering = ['-priority', '-created_at']

    def comment_preview(self, obj):
        """Preview do comentário"""
        content = obj.comment.content[:80]
        if len(obj.comment.content) > 80:
            content += '...'
        return format_html('<div style="max-width: 250px;">{}</div>', content)
    comment_preview.short_description = 'Comentário'

    def priority_display(self, obj):
        """Display colorido da prioridade"""
        colors = {
            'low': 'green',
            'medium': 'orange',
            'high': 'red',
            'critical': 'darkred'
        }
        color = colors.get(obj.priority, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_priority_display()
        )
    priority_display.short_description = 'Prioridade'

    def status_display(self, obj):
        """Display colorido do status"""
        colors = {
            'pending': 'orange',
            'in_review': 'blue',
            'resolved': 'green',
            'escalated': 'red'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Status'

    def assigned_to_info(self, obj):
        """Informações do moderador atribuído"""
        if obj.assigned_to:
            admin_url = reverse('admin:auth_user_change', args=[obj.assigned_to.pk])
            return format_html(
                '<a href="{}">{}</a>',
                admin_url, obj.assigned_to.username
            )
        return '-'
    assigned_to_info.short_description = 'Atribuído a'

    def actions_display(self, obj):
        """Ações disponíveis"""
        if obj.status == 'pending':
            return '🔍 Revisar'
        elif obj.status == 'in_review':
            return '✅ Resolver'
        return '-'
    actions_display.short_description = 'Ações'


@admin.register(CommentModeration)
class CommentModerationAdmin(admin.ModelAdmin):
    """Admin para configurações de moderação"""
    list_display = [
        'app_label', 'model_name', 'moderation_type',
        'auto_approve_trusted_users', 'created_at'
    ]
    list_filter = ['moderation_type', 'auto_approve_trusted_users', 'created_at']
    search_fields = ['app_label', 'model_name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['app_label', 'model_name']

    fieldsets = (
        ('Informações da Regra', {
            'fields': ('name', 'description', 'rule_type', 'severity', 'is_active')
        }),
        ('Configuração', {
            'fields': ('pattern', 'threshold', 'action'),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def rule_type_display(self, obj):
        """Display do tipo de regra"""
        return obj.get_rule_type_display()
    rule_type_display.short_description = 'Tipo'

    def severity_display(self, obj):
        """Display colorido da severidade"""
        colors = {
            'low': 'green',
            'medium': 'orange',
            'high': 'red',
            'critical': 'darkred'
        }
        color = colors.get(obj.severity, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_severity_display()
        )
    severity_display.short_description = 'Severidade'


@admin.register(CommentNotification)
class CommentNotificationAdmin(admin.ModelAdmin):
    """Admin para notificações"""
    list_display = [
        'notification_preview', 'user_info', 'notification_type_display',
        'is_read', 'created_at'
    ]
    list_filter = [
        'notification_type', 'is_read', 'created_at',
        ('recipient', admin.RelatedOnlyFieldListFilter)
    ]
    search_fields = ['message', 'recipient__username', 'recipient__email']
    readonly_fields = ['created_at', 'read_at']
    raw_id_fields = ['recipient', 'comment']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    list_per_page = 50

    actions = ['mark_as_read', 'mark_as_unread']

    def notification_preview(self, obj):
        """Preview da notificação"""
        message = obj.message[:100]
        if len(obj.message) > 100:
            message += '...'
        return format_html('<div style="max-width: 300px;">{}</div>', message)
    notification_preview.short_description = 'Mensagem'

    def user_info(self, obj):
        """Informações do usuário"""
        admin_url = reverse('admin:auth_user_change', args=[obj.user.pk])
        return format_html(
            '<a href="{}">{}</a>',
            admin_url, obj.user.username
        )
    user_info.short_description = 'Usuário'

    def notification_type_display(self, obj):
        """Display do tipo de notificação"""
        icons = {
            'comment_reply': '💬',
            'comment_mention': '📢',
            'comment_like': '👍',
            'comment_moderation': '🛡️'
        }
        icon = icons.get(obj.notification_type, '📝')
        return format_html(
            '{} {}',
            icon, obj.get_notification_type_display()
        )
    notification_type_display.short_description = 'Tipo'

    def mark_as_read(self, request, queryset):
        """Marcar como lida"""
        updated = queryset.filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        self.message_user(
            request,
            f'{updated} notificação(ões) marcada(s) como lida(s).'
        )
    mark_as_read.short_description = "✅ Marcar como lida"

    def mark_as_unread(self, request, queryset):
        """Marcar como não lida"""
        updated = queryset.filter(is_read=True).update(
            is_read=False,
            read_at=None
        )
        self.message_user(
            request,
            f'{updated} notificação(ões) marcada(s) como não lida(s).'
        )
    mark_as_unread.short_description = "📧 Marcar como não lida"


# Configurações do admin site
admin.site.site_header = 'Sistema de Comentários - Administração'
admin.site.site_title = 'Comentários Admin'
admin.site.index_title = 'Painel de Administração'