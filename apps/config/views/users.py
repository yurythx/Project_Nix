from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from apps.config.services.user_management_service import UserManagementService
from apps.config.repositories.user_repository import DjangoUserRepository  # Corrigido
from apps.config.services import AuditService

User = get_user_model()

class UserListView(ListView):
    model = User
    template_name = 'config/users/list.html'
    context_object_name = 'users'
    
    def get_queryset(self):
        audit_service = AuditService()
        user_service = UserManagementService(DjangoUserRepository(), audit_service)
        return user_service.list_users()

class UserCreateView(CreateView):
    model = User
    template_name = 'config/users/create.html'
    fields = ['username', 'email', 'first_name', 'last_name']
    success_url = reverse_lazy('config:users:list')
    
    def form_valid(self, form):
        audit_service = AuditService()
        user_service = UserManagementService(DjangoUserRepository(), audit_service)
        user_data = form.cleaned_data
        user_service.create_user(user_data, self.request.user)
        return super().form_valid(form)

class UserUpdateView(UpdateView):
    model = User
    template_name = 'config/users/update.html'
    fields = ['username', 'email', 'first_name', 'last_name']
    success_url = reverse_lazy('config:users:list')
    
    def form_valid(self, form):
        audit_service = AuditService()
        user_service = UserManagementService(DjangoUserRepository(), audit_service)
        user_data = form.cleaned_data
        user_service.update_user(self.object.id, user_data, self.request.user)
        return super().form_valid(form)

class UserDeleteView(DeleteView):
    model = User
    template_name = 'config/users/delete.html'
    success_url = reverse_lazy('config:users:list')
    
    def delete(self, request, *args, **kwargs):
        audit_service = AuditService()
        user_service = UserManagementService(DjangoUserRepository(), audit_service)
        user_service.delete_user(self.get_object().id, request.user)
        return super().delete(request, *args, **kwargs)

 