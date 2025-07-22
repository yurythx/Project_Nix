from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from apps.mangas.models.manga import Manga, Capitulo, Pagina
from apps.mangas.forms.manga_form import MangaForm, CapituloForm, PaginaForm

# Mangá
class MangaListView(ListView):
    model = Manga
    template_name = 'mangas/manga_list.html'
    context_object_name = 'mangas'
    paginate_by = 12
    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(title__icontains=q)
        return queryset

class MangaDetailView(DetailView):
    model = Manga
    template_name = 'mangas/manga_detail.html'
    context_object_name = 'manga'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

class MangaCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Manga
    form_class = MangaForm
    template_name = 'mangas/manga_form.html'
    success_url = reverse_lazy('mangas:manga_list')
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

class MangaUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Manga
    form_class = MangaForm
    template_name = 'mangas/manga_form.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    success_url = reverse_lazy('mangas:manga_list')
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

class MangaDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Manga
    template_name = 'mangas/manga_confirm_delete.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    success_url = reverse_lazy('mangas:manga_list')
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

# Capítulo
class CapituloDetailView(DetailView):
    model = Capitulo
    template_name = 'mangas/capitulo_detail.html'
    context_object_name = 'capitulo'
    slug_field = 'slug'
    slug_url_kwarg = 'capitulo_slug'
    def get_queryset(self):
        manga_slug = self.kwargs.get('manga_slug')
        return Capitulo.objects.filter(manga__slug=manga_slug)

class CapituloCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Capitulo
    form_class = CapituloForm
    template_name = 'mangas/manga_form.html'
    def get_initial(self):
        manga = Manga.objects.get(slug=self.kwargs['manga_slug'])
        return {'manga': manga}
    def form_valid(self, form):
        form.instance.manga = Manga.objects.get(slug=self.kwargs['manga_slug'])
        return super().form_valid(form)
    def get_success_url(self):
        return self.object.manga.get_absolute_url()
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

class CapituloUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Capitulo
    form_class = CapituloForm
    template_name = 'mangas/manga_form.html'
    slug_field = 'slug'
    slug_url_kwarg = 'capitulo_slug'
    def get_queryset(self):
        manga_slug = self.kwargs.get('manga_slug')
        return Capitulo.objects.filter(manga__slug=manga_slug)
    def get_success_url(self):
        return self.object.manga.get_absolute_url()
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

class CapituloDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Capitulo
    template_name = 'mangas/manga_confirm_delete.html'
    slug_field = 'slug'
    slug_url_kwarg = 'capitulo_slug'
    def get_queryset(self):
        manga_slug = self.kwargs.get('manga_slug')
        return Capitulo.objects.filter(manga__slug=manga_slug)
    def get_success_url(self):
        return self.object.manga.get_absolute_url()
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

# Página
class PaginaCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Pagina
    form_class = PaginaForm
    template_name = 'mangas/manga_form.html'
    def get_initial(self):
        capitulo = Capitulo.objects.get(slug=self.kwargs['capitulo_slug'])
        return {'capitulo': capitulo}
    def form_valid(self, form):
        form.instance.capitulo = Capitulo.objects.get(slug=self.kwargs['capitulo_slug'])
        return super().form_valid(form)
    def get_success_url(self):
        return self.object.capitulo.get_absolute_url()
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

class PaginaUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Pagina
    form_class = PaginaForm
    template_name = 'mangas/manga_form.html'
    def get_queryset(self):
        capitulo_slug = self.kwargs.get('capitulo_slug')
        return Pagina.objects.filter(capitulo__slug=capitulo_slug)
    def get_success_url(self):
        return self.object.capitulo.get_absolute_url()
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

class PaginaDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Pagina
    template_name = 'mangas/manga_confirm_delete.html'
    def get_queryset(self):
        capitulo_slug = self.kwargs.get('capitulo_slug')
        return Pagina.objects.filter(capitulo__slug=capitulo_slug)
    def get_success_url(self):
        return self.object.capitulo.get_absolute_url()
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser 