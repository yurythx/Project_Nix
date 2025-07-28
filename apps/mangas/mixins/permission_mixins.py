"""
Módulo contendo mixins personalizados para controle de permissões nas views.
"""
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy


class StaffOrSuperuserRequiredMixin(UserPassesTestMixin):
    """
    Mixin que verifica se o usuário é membro da equipe (staff) ou superusuário.
    """
    permission_denied_message = "Você não tem permissão para acessar esta página."
    redirect_url = 'mangas:manga_list'
    
    def test_func(self):
        """Verifica se o usuário é staff ou superusuário."""
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def handle_no_permission(self):
        """Redireciona o usuário com uma mensagem de erro se não tiver permissão."""
        messages.error(self.request, self.permission_denied_message)
        return redirect(self.redirect_url)


class MangaOwnerOrStaffMixin(StaffOrSuperuserRequiredMixin):
    """
    Mixin que verifica se o usuário é o proprietário do mangá ou um membro da equipe.
    """
    permission_denied_message = "Você só pode editar ou excluir mangás que você criou."
    
    def test_func(self):
        """Verifica se o usuário é o criador do mangá ou um membro da equipe/superusuário."""
        if not self.request.user.is_authenticated:
            return False
            
        # Se for staff ou superusuário, permite o acesso
        if super().test_func():
            return True
            
        # Para outros usuários, verifica se é o criador do mangá
        try:
            obj = self.get_object()
            return obj.criado_por == self.request.user
        except Exception:
            return False


class ChapterOwnerOrStaffMixin(StaffOrSuperuserRequiredMixin):
    """
    Mixin que verifica se o usuário é o proprietário do capítulo ou tem permissão de staff.
    """
    permission_denied_message = "Você só pode editar ou excluir capítulos de mangás que você criou."
    
    def test_func(self):
        """
        Verifica se o usuário é o criador do mangá relacionado ao capítulo 
        ou um membro da equipe.
        """
        if not self.request.user.is_authenticated:
            return False
            
        # Se for staff ou superusuário, permite o acesso
        if super().test_func():
            return True
            
        # Para outros usuários, verifica se é o criador do mangá relacionado
        try:
            obj = self.get_object()
            return obj.manga.criado_por == self.request.user
        except Exception:
            return False


class PageOwnerOrStaffMixin(StaffOrSuperuserRequiredMixin):
    """
    Mixin que verifica se o usuário é o proprietário da página ou tem permissão de staff.
    """
    permission_denied_message = "Você só pode editar ou excluir páginas de capítulos que você criou."
    
    def test_func(self):
        """
        Verifica se o usuário é o criador do mangá relacionado à página 
        ou um membro da equipe.
        """
        if not self.request.user.is_authenticated:
            return False
            
        # Se for staff ou superusuário, permite o acesso
        if super().test_func():
            return True
            
        # Para outros usuários, verifica se é o criador do mangá relacionado
        try:
            obj = self.get_object()
            return obj.capitulo.manga.criado_por == self.request.user
        except Exception:
            return False
