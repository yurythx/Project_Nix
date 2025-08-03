from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.http import Http404, HttpResponseRedirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from apps.audiobooks.models.category import Category
from apps.audiobooks.services.category_service import CategoryService
from apps.audiobooks.forms.category_form import CategoryForm

class BaseCategoryView:
    """
    View base para categorias implementando princípios SOLID
    
    Princípios SOLID aplicados:
    - Single Responsibility: Funcionalidades base para views de categorias
    - Dependency Inversion: Usa serviço via injeção de dependência
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.category_service = CategoryService()

class CategoryListView(BaseCategoryView, ListView):
    """
    View para listar categorias
    
    Princípios SOLID aplicados:
    - Single Responsibility: Apenas listagem de categorias
    - Open/Closed: Extensível via herança
    """
    model = Category
    template_name = 'audiobooks/category_list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        return self.category_service.get_active_categories()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Categorias')
        return context

class CategoryDetailView(BaseCategoryView, DetailView):
    """
    View para exibir detalhes de uma categoria
    
    Princípios SOLID aplicados:
    - Single Responsibility: Apenas exibição de detalhes da categoria
    - Open/Closed: Extensível via herança
    """
    model = Category
    template_name = 'audiobooks/category_detail.html'
    context_object_name = 'category'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_object(self, queryset=None):
        slug = self.kwargs.get(self.slug_url_kwarg)
        category = self.category_service.get_category_by_slug(slug)
        if not category:
            raise Http404(_('Categoria não encontrada'))
        return category
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.object
        context['videos'] = category.videos.filter(is_public=True)
        context['title'] = category.name
        return context

class CategoryCreateView(LoginRequiredMixin, UserPassesTestMixin, BaseCategoryView, CreateView):
    """
    View para criar uma nova categoria
    
    Princípios SOLID aplicados:
    - Single Responsibility: Apenas criação de categorias
    - Open/Closed: Extensível via herança
    """
    model = Category
    form_class = CategoryForm
    template_name = 'audiobooks/category_form.html'
    success_url = reverse_lazy('audiobooks:category_list')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def form_valid(self, form):
        messages.success(self.request, _('Categoria criada com sucesso!'))
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Nova Categoria')
        context['button_text'] = _('Criar')
        return context

class CategoryUpdateView(LoginRequiredMixin, UserPassesTestMixin, BaseCategoryView, UpdateView):
    """
    View para atualizar uma categoria existente
    
    Princípios SOLID aplicados:
    - Single Responsibility: Apenas atualização de categorias
    - Open/Closed: Extensível via herança
    """
    model = Category
    form_class = CategoryForm
    template_name = 'audiobooks/category_form.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_success_url(self):
        return reverse_lazy('audiobooks:category_detail', kwargs={'slug': self.object.slug})
    
    def form_valid(self, form):
        messages.success(self.request, _('Categoria atualizada com sucesso!'))
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Editar Categoria')
        context['button_text'] = _('Atualizar')
        return context

class CategoryDeleteView(LoginRequiredMixin, UserPassesTestMixin, BaseCategoryView, DeleteView):
    """
    View para excluir uma categoria
    
    Princípios SOLID aplicados:
    - Single Responsibility: Apenas exclusão de categorias
    - Open/Closed: Extensível via herança
    """
    model = Category
    template_name = 'audiobooks/category_confirm_delete.html'
    success_url = reverse_lazy('audiobooks:category_list')
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        
        # Usa o serviço para excluir
        if self.category_service.delete_category(self.object.id):
            messages.success(request, _('Categoria excluída com sucesso!'))
        else:
            messages.error(request, _('Erro ao excluir categoria.'))
            
        return HttpResponseRedirect(success_url)