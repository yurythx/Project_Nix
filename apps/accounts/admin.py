from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from apps.accounts.models import User, VerificationCode

class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_verified', 'is_staff')
    list_filter = ('is_verified', 'is_staff', 'is_superuser')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password', 'slug')}),
        ('Informações Pessoais', {'fields': ('first_name', 'last_name', 'username')}),
        ('Permissões', {'fields': ('is_verified', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Datas Importantes', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )

class VerificationCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'code_type', 'code', 'created_at', 'expires_at')
    list_filter = ('code_type',)
    search_fields = ('user__email', 'code')
    readonly_fields = ('created_at', 'expires_at')

admin.site.register(User, CustomUserAdmin)