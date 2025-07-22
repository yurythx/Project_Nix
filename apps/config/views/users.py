from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from apps.config.services.user_service import UserService
from apps.config.models.group import Group
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

User = get_user_model()

class UserListView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'config/users/list.html'
    context_object_name = 'users'

    def get_queryset(self):
        return UserService.list_users()

class UserCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = User
    fields = ['username', 'email', 'password', 'groups']
    template_name = 'config/users/create.html'
    success_url = reverse_lazy('config:user_list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

class UserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    fields = ['username', 'email', 'groups']
    template_name = 'config/users/update.html'
    success_url = reverse_lazy('config:user_list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

class UserDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = User
    template_name = 'config/users/delete.html'
    success_url = reverse_lazy('config:user_list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

 