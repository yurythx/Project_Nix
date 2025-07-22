from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.shortcuts import render
from apps.audiobooks.models import Audiobook
from apps.audiobooks.forms.audiobook_form import AudiobookForm

class AudiobookListView(ListView):
    model = Audiobook
    template_name = 'audiobooks/audiobook_list.html'
    context_object_name = 'audiobooks'
    paginate_by = 12

    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(title__icontains=q)
        return queryset

class AudiobookDetailView(DetailView):
    model = Audiobook
    template_name = 'audiobooks/audiobook_detail.html'
    context_object_name = 'audiobook'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

class AudiobookCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Audiobook
    form_class = AudiobookForm
    template_name = 'audiobooks/audiobook_form.html'
    success_url = reverse_lazy('audiobooks:audiobook_list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

class AudiobookUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Audiobook
    form_class = AudiobookForm
    template_name = 'audiobooks/audiobook_form.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

class AudiobookDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Audiobook
    template_name = 'audiobooks/audiobook_confirm_delete.html'
    success_url = reverse_lazy('audiobooks:audiobook_list')
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
