from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from apps.accounts.forms.profile_forms import (
    ProfileUpdateForm, AvatarUpdateForm, EmailUpdateForm, PasswordChangeForm
)
from apps.accounts.services.profile_service import ProfileService
from apps.accounts.repositories.user_repository import DjangoUserRepository
import os
from django.views.generic.detail import DetailView

User = get_user_model()

class UserProfileView(LoginRequiredMixin, DetailView):
    """View para exibir perfil do usuário"""
    template_name = 'accounts/profile.html'
    context_object_name = 'profile_user'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    login_url = '/accounts/login/'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Injeção de dependência
        self.profile_service = ProfileService(DjangoUserRepository())

    def get_object(self, queryset=None):
        slug = self.kwargs.get('slug')
        if slug:
            return self.profile_service.get_profile(slug)
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object
        context['avatar_form'] = AvatarUpdateForm(instance=user)
        context['user_stats'] = self.profile_service.get_user_statistics(user)
        return context

class UserUpdateView(LoginRequiredMixin, View):
    template_name = 'accounts/user_settings.html'
    login_url = '/accounts/login/'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.profile_service = ProfileService(DjangoUserRepository())

    def get(self, request):
        return render(request, self.template_name, self.get_context_with_forms(request.user))

    def post(self, request):
        user = request.user
        form_type = request.POST.get('form_type')
        context = self.get_context_with_forms(user)

        if form_type == 'profile':
            form = ProfileUpdateForm(request.POST, instance=user)
            if form.is_valid():
                self.profile_service.update_profile(user, form.cleaned_data)
                messages.success(request, '🎉 Perfil atualizado com sucesso!')
                return redirect('accounts:profile')
            context['profile_form'] = form

        elif form_type == 'avatar':
            form = AvatarUpdateForm(request.POST, request.FILES, instance=user)
            if form.is_valid():
                form.save()
                messages.success(request, '📸 Foto de perfil atualizada com sucesso!')
                return redirect('accounts:profile')
            context['avatar_form'] = form

        elif form_type == 'email':
            form = EmailUpdateForm(user=user, data=request.POST, instance=user)
            if form.is_valid():
                messages.success(request, f'📧 Código de verificação enviado para {form.cleaned_data["email"]}!')
                return redirect('accounts:profile')
            context['email_form'] = form

        elif form_type == 'password':
            form = PasswordChangeForm(user=user, data=request.POST)
            if form.is_valid():
                user.set_password(form.cleaned_data['new_password1'])
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, '🔒 Senha alterada com sucesso!')
                return redirect('accounts:profile')
            context['password_form'] = form

        else:
            messages.error(request, 'Tipo de formulário inválido.')

        return render(request, self.template_name, context)

    def get_context_with_forms(self, user):
        return {
            'profile_form': ProfileUpdateForm(instance=user),
            'avatar_form': AvatarUpdateForm(instance=user),
            'email_form': EmailUpdateForm(user=user, instance=user),
            'password_form': PasswordChangeForm(user=user),
            'profile_user': user,
        }

class RemoveAvatarView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.profile_service = ProfileService(DjangoUserRepository())

    def post(self, request):
        user = request.user
        try:
            success = self.profile_service.remove_avatar(user)
            if success:
                messages.success(request, '🗑️ Foto de perfil removida com sucesso! Agora você está usando o avatar padrão.')
            else:
                messages.info(request, 'ℹ️ Você não possui foto de perfil para remover.')
        except Exception as e:
            messages.error(request, f'❌ Erro ao remover foto de perfil: {str(e)}')
        return redirect('accounts:settings')
