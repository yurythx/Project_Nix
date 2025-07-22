from django.contrib import admin
from apps.articles.models import Article, Category, Tag, Comment

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin para categorias"""
    list_display = ['name', 'slug', 'parent', 'is_active', 'order', 'article_count']
    list_filter = ['is_active', 'parent']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']

    def article_count(self, obj):
        return obj.get_article_count()
    article_count.short_description = 'Artigos'

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Admin para tags"""
    list_display = ['name', 'slug', 'is_featured', 'article_count', 'created_at']
    list_filter = ['is_featured', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}

    def article_count(self, obj):
        return obj.get_article_count()
    article_count.short_description = 'Artigos'

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """Admin para artigos"""
    list_display = ['title', 'author', 'category', 'status', 'is_featured', 'view_count', 'published_at']
    list_filter = ['status', 'is_featured', 'category', 'created_at', 'published_at']
    search_fields = ['title', 'excerpt', 'content']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['view_count', 'reading_time', 'created_at', 'updated_at']
    filter_horizontal = ['tags', 'contributors']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('title', 'slug', 'excerpt', 'content', 'featured_image', 'featured_image_alt')
        }),
        ('Classificação', {
            'fields': ('category', 'tags')
        }),
        ('Autoria', {
            'fields': ('author', 'contributors')
        }),
        ('Publicação', {
            'fields': ('status', 'is_featured', 'allow_comments', 'published_at', 'scheduled_at')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('Estatísticas', {
            'fields': ('view_count', 'reading_time', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # Criando novo
            obj.author = request.user
        super().save_model(request, obj, form, change)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin para comentários"""
    list_display = [
        'comment_preview', 'author_info', 'article_link', 'status_display',
        'reply_info', 'created_at', 'actions_display'
    ]
    list_filter = [
        'is_approved', 'is_spam', 'created_at', 'article__category',
        ('user', admin.RelatedOnlyFieldListFilter),
        ('parent', admin.RelatedOnlyFieldListFilter)
    ]
    search_fields = ['name', 'email', 'content', 'article__title']
    readonly_fields = [
        'ip_address', 'user_agent', 'created_at', 'updated_at',
        'approved_at', 'reply_count_display'
    ]
    raw_id_fields = ['article', 'parent', 'user']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Informações do Comentário', {
            'fields': ('article', 'parent', 'content')
        }),
        ('Autor', {
            'fields': ('user', 'name', 'email', 'website')
        }),
        ('Moderação', {
            'fields': ('is_approved', 'is_spam', 'approved_at')
        }),
        ('Dados Técnicos', {
            'fields': ('ip_address', 'user_agent', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Estatísticas', {
            'fields': ('reply_count_display',),
            'classes': ('collapse',)
        }),
    )

    actions = ['approve_comments', 'mark_as_spam', 'mark_as_not_spam', 'delete_selected']

    def get_queryset(self, request):
        """Otimizar queries"""
        return super().get_queryset(request).select_related(
            'article', 'user', 'parent'
        ).prefetch_related('replies')

    def comment_preview(self, obj):
        """Preview do comentário"""
        preview = obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
        return preview
    comment_preview.short_description = 'Comentário'

    def author_info(self, obj):
        """Informações do autor"""
        if obj.user:
            return f"{obj.author_name} (Registrado)"
        return f"{obj.author_name} ({obj.email})"
    author_info.short_description = 'Autor'

    def article_link(self, obj):
        """Link para o artigo"""
        from django.utils.html import format_html
        return format_html(
            '<a href="{}" target="_blank">{}</a>',
            obj.article.get_absolute_url(),
            obj.article.title[:50] + '...' if len(obj.article.title) > 50 else obj.article.title
        )
    article_link.short_description = 'Artigo'

    def status_display(self, obj):
        """Status visual"""
        from django.utils.html import format_html
        if obj.is_spam:
            return format_html('<span style="color: red;">🚫 Spam</span>')
        elif obj.is_approved:
            return format_html('<span style="color: green;">✅ Aprovado</span>')
        else:
            return format_html('<span style="color: orange;">⏳ Pendente</span>')
    status_display.short_description = 'Status'

    def reply_info(self, obj):
        """Informações sobre respostas"""
        if obj.parent:
            return f"↳ Resposta a {obj.parent.author_name}"
        elif obj.reply_count > 0:
            return f"{obj.reply_count} resposta(s)"
        return "-"
    reply_info.short_description = 'Respostas'

    def actions_display(self, obj):
        """Ações rápidas"""
        from django.utils.html import format_html
        from django.urls import reverse

        actions = []
        if not obj.is_approved and not obj.is_spam:
            approve_url = reverse('admin:articles_comment_changelist')
            actions.append(f'<a href="#" onclick="approveComment({obj.id})">Aprovar</a>')

        if not obj.is_spam:
            actions.append(f'<a href="#" onclick="markSpam({obj.id})">Spam</a>')

        view_url = obj.article.get_absolute_url() + f'#comment-{obj.id}'
        actions.append(f'<a href="{view_url}" target="_blank">Ver</a>')

        return format_html(' | '.join(actions))
    actions_display.short_description = 'Ações'

    def reply_count_display(self, obj):
        """Contagem de respostas"""
        return obj.reply_count
    reply_count_display.short_description = 'Número de Respostas'

    def approve_comments(self, request, queryset):
        """Aprovar comentários selecionados"""
        from django.utils import timezone
        updated = queryset.filter(is_spam=False).update(
            is_approved=True,
            approved_at=timezone.now()
        )
        self.message_user(request, f'{updated} comentário(s) aprovado(s).')
    approve_comments.short_description = "✅ Aprovar comentários selecionados"

    def mark_as_spam(self, request, queryset):
        """Marcar como spam"""
        updated = queryset.update(is_spam=True, is_approved=False, approved_at=None)
        self.message_user(request, f'{updated} comentário(s) marcado(s) como spam.')
    mark_as_spam.short_description = "🚫 Marcar como spam"

    def mark_as_not_spam(self, request, queryset):
        """Remover marca de spam"""
        updated = queryset.update(is_spam=False)
        self.message_user(request, f'{updated} comentário(s) desmarcado(s) como spam.')
    mark_as_not_spam.short_description = "✅ Não é spam"

    class Media:
        js = ('admin/js/comment_admin.js',)
        css = {
            'all': ('admin/css/comment_admin.css',)
        }
