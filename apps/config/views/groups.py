from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from apps.config.models.group import Group
from apps.config.services.group_service import GroupService
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

class GroupListView(LoginRequiredMixin, ListView):
    model = Group
    template_name = 'config/groups/list.html'
    context_object_name = 'groups'

    def get_queryset(self):
        return GroupService.list_groups()

class GroupDetailView(LoginRequiredMixin, DetailView):
    model = Group
    template_name = 'config/groups/detail.html'
    context_object_name = 'group'
    slug_url_kwarg = 'slug'

class GroupCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Group
    fields = ['name', 'description']
    template_name = 'config/groups/create.html'
    success_url = reverse_lazy('config:group_list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

class GroupUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Group
    fields = ['name', 'description']
    template_name = 'config/groups/update.html'
    success_url = reverse_lazy('config:group_list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

class GroupDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Group
    template_name = 'config/groups/delete.html'
    success_url = reverse_lazy('config:group_list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser 