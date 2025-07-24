"""
Views para artigos seguindo princípios SOLID e CBV
"""
from typing import Dict, Any, Optional
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse, Http404
from django.db.models import QuerySet, Q
from django.core.exceptions import PermissionDenied

from apps.articles.interfaces.services import IArticleService, ICategoryService, IContentProcessorService
from apps.articles.models.article import Article
from apps.articles.models.category import Category
from apps.articles.forms import ArticleForm
from apps.common.mixins import ModuleEnabledRequiredMixin
from core.factories import service_factory

class BaseArticleView(ModuleEnabledRequiredMixin):
    """
    View base para artigos implementando princípios SOLID

    Princípios aplicados:
    - Single Responsibility: Funcionalidades base para views de artigos
    - Dependency Inversion: Usa interfaces de services
    - Open/Closed: Extensível para views específicas
    """
    module_name = 'apps.articles'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._article_service: Optional[IArticleService] = None
        self._category_service: Optional[ICategoryService] = None
        self._content_processor: Optional[IContentProcessorService] = None

    @property
    def article_service(self) -> IArticleService:
        """Lazy loading do service de artigos"""
        if self._article_service is None:
            self._article_service = service_factory.create_article_service()
        return self._article_service

    @property
    def category_service(self) -> ICategoryService:
        """Lazy loading do service de categorias"""
        if self._category_service is None:
            self._category_service = service_factory.create_category_service()
        return self._category_service

    @property
    def content_processor(self) -> IContentProcessorService:
        """Lazy loading do processador de conteúdo"""
        if self._content_processor is None:
            self._content_processor = service_factory.create_content_processor_service()
        return self._content_processor


class ArticleListView(BaseArticleView, ListView):
    """
    View para listagem de artigos

    Princípios SOLID aplicados:
    - Single Responsibility: Apenas listagem de artigos
    - Open/Closed: Extensível via herança
    - Liskov Substitution: Pode ser substituída por outras implementações
    """
    model = Article
    template_name = 'articles/article_list.html'
    context_object_name = 'articles'
    paginate_by = 12

    def get_queryset(self) -> QuerySet[Article]:
        """Retorna queryset de artigos publicados"""
        return self.article_service.get_published_articles()

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Adiciona dados específicos do contexto"""
        context = super().get_context_data(**kwargs)

        # Dados específicos da listagem
        context.update({
            'featured_articles': self.article_service.get_featured_articles(limit=3),
            'categories': self.category_service.get_categories_with_articles(),
            'meta_title': 'Artigos',
            'meta_description': 'Todos os artigos do blog',
        })

        return context

class ArticleDetailView(BaseArticleView, DetailView):
    """
    View para exibir detalhes de um artigo

    Princípios SOLID aplicados:
    - Single Responsibility: Apenas exibe detalhes do artigo
    - Dependency Inversion: Usa services através de interfaces
    - Open/Closed: Extensível para customizações específicas
    """
    model = Article
    template_name = 'articles/article_detail.html'
    context_object_name = 'article'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_object(self, queryset=None) -> Article:
        """
        Obtém o artigo usando service

        Raises:
            Http404: Se artigo não for encontrado
        """
        try:
            return self.article_service.get_article_by_slug(self.kwargs['slug'])
        except Article.DoesNotExist:
            raise Http404("Artigo não encontrado")

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Adiciona dados específicos do contexto"""
        context = super().get_context_data(**kwargs)
        article = self.object

        # Incrementa visualizações
        self.article_service.increment_article_views(article.id)

        # Processa conteúdo para exibição limpa
        context['processed_content'] = self.content_processor.process_for_display(article.content)

        # Dados relacionados
        context.update({
            'related_articles': self.article_service.get_related_articles(article, limit=3),
            'comments': article.comments.filter(is_approved=True, parent__isnull=True).order_by('-created_at')[:5],
            'comment_count': article.comments.filter(is_approved=True).count(),
        })

        # SEO metadata
        context.update({
            'meta_title': article.seo_title or article.title,
            'meta_description': article.seo_description or article.excerpt,
            'meta_keywords': getattr(article, 'meta_keywords', '') or '',
        })

        return context


class ArticleSearchView(BaseArticleView, ListView):
    """
    View para busca de artigos

    Princípios SOLID aplicados:
    - Single Responsibility: Apenas busca de artigos
    - Open/Closed: Extensível para diferentes tipos de busca
    """
    model = Article
    template_name = 'articles/article_search.html'
    context_object_name = 'articles'
    paginate_by = 12

    def get_queryset(self) -> QuerySet[Article]:
        """Retorna queryset filtrado pela busca"""
        query = self.request.GET.get('q', '').strip()
        category = self.request.GET.get('category', '')
        tag = self.request.GET.get('tag', '')

        if not query and not category and not tag:
            return Article.objects.none()

        filters = {}
        if category:
            filters['category'] = category
        if tag:
            filters['tag'] = tag

        return self.article_service.search_articles(query, **filters)

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Adiciona dados específicos da busca"""
        context = super().get_context_data(**kwargs)

        query = self.request.GET.get('q', '').strip()
        context.update({
            'search_query': query,
            'categories': self.category_service.get_categories_with_articles(),
            'meta_title': f'Busca: {query}' if query else 'Buscar artigos',
            'meta_description': f'Resultados da busca por "{query}"' if query else 'Buscar artigos',
        })

        return context


class EditorOrAdminRequiredMixin(UserPassesTestMixin):
    """
    Mixin para controle de acesso de editores e administradores

    Princípios SOLID aplicados:
    - Single Responsibility: Apenas controle de acesso
    - Open/Closed: Extensível para outros tipos de permissão
    """

    def test_func(self) -> bool:
        """Testa se usuário tem permissão"""
        user = self.request.user

        if not user.is_authenticated:
            return False

        # Superuser e staff sempre têm acesso
        if user.is_superuser or user.is_staff:
            return True

        # Verifica grupos específicos
        allowed_groups = ['administrador', 'admin', 'editor']
        query = Q()
        for group in allowed_groups:
            query |= Q(name__iexact=group)
        return user.groups.filter(query).exists()

    def handle_no_permission(self):
        """Trata acesso negado"""
        messages.error(
            self.request,
            '🚫 Acesso negado! Apenas administradores ou editores podem realizar esta ação.'
        )
        raise PermissionDenied("Acesso negado")


class ArticleCreateView(EditorOrAdminRequiredMixin, BaseArticleView, CreateView):
    """
    View para criação de artigos

    Princípios SOLID aplicados:
    - Single Responsibility: Apenas criação de artigos
    - Dependency Inversion: Usa service para lógica de negócio
    """
    model = Article
    form_class = ArticleForm
    template_name = 'articles/article_form.html'
    success_url = reverse_lazy('articles:article_list')

    def form_valid(self, form) -> Any:
        """Processa formulário válido"""
        try:
            # Define autor como usuário atual
            form.instance.author = self.request.user

            # Usa service para criar artigo
            article_data = form.cleaned_data
            article = self.article_service.create_article(article_data, self.request.user)

            messages.success(self.request, f'Artigo "{article.title}" criado com sucesso!')
            return redirect('articles:article_detail', slug=article.slug)

        except Exception as e:
            messages.error(self.request, f'Erro ao criar artigo: {str(e)}')
            return self.form_invalid(form)

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Adiciona dados específicos do contexto"""
        context = super().get_context_data(**kwargs)
        context.update({
            'meta_title': 'Criar Artigo',
            'meta_description': 'Criar novo artigo',
            'form_action': 'Criar',
        })
        return context


class ArticleUpdateView(EditorOrAdminRequiredMixin, BaseArticleView, UpdateView):
    """
    View para edição de artigos

    Princípios SOLID aplicados:
    - Single Responsibility: Apenas edição de artigos
    - Dependency Inversion: Usa service para lógica de negócio
    """
    model = Article
    form_class = ArticleForm
    template_name = 'articles/article_form.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_object(self, queryset=None) -> Article:
        """Obtém artigo para edição"""
        try:
            return self.article_service.get_article_by_slug(self.kwargs['slug'])
        except Article.DoesNotExist:
            raise Http404("Artigo não encontrado")

    def form_valid(self, form) -> Any:
        """Processa formulário válido"""
        try:
            article_data = form.cleaned_data
            article = self.article_service.update_article(
                self.object.id,
                article_data,
                self.request.user
            )

            messages.success(self.request, f'Artigo "{article.title}" atualizado com sucesso!')
            return redirect('articles:article_detail', slug=article.slug)

        except Exception as e:
            messages.error(self.request, f'Erro ao atualizar artigo: {str(e)}')
            return self.form_invalid(form)

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Adiciona dados específicos do contexto"""
        context = super().get_context_data(**kwargs)
        context.update({
            'meta_title': f'Editar: {self.object.title}',
            'meta_description': f'Editar artigo {self.object.title}',
            'form_action': 'Atualizar',
        })
        return context


class ArticleDeleteView(EditorOrAdminRequiredMixin, BaseArticleView, DeleteView):
    """
    View para exclusão de artigos

    Princípios SOLID aplicados:
    - Single Responsibility: Apenas exclusão de artigos
    - Dependency Inversion: Usa service para lógica de negócio
    """
    model = Article
    template_name = 'articles/article_confirm_delete.html'
    success_url = reverse_lazy('articles:article_list')
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_object(self, queryset=None) -> Article:
        """Obtém artigo para exclusão"""
        try:
            return self.article_service.get_article_by_slug(self.kwargs['slug'])
        except Article.DoesNotExist:
            raise Http404("Artigo não encontrado")

    def delete(self, request, *args, **kwargs) -> Any:
        """Processa exclusão do artigo"""
        article = self.get_object()
        article_title = article.title

        try:
            success = self.article_service.delete_article(article.id, request.user)

            if success:
                messages.success(request, f'Artigo "{article_title}" excluído com sucesso!')
            else:
                messages.error(request, 'Erro ao excluir artigo.')

        except Exception as e:
            messages.error(request, f'Erro ao excluir artigo: {str(e)}')

        return redirect(self.success_url)

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Adiciona dados específicos do contexto"""
        context = super().get_context_data(**kwargs)
        context.update({
            'meta_title': f'Excluir: {self.object.title}',
            'meta_description': f'Confirmar exclusão do artigo {self.object.title}',
        })
        return context


class CategoryDetailView(BaseArticleView, DetailView):
    """
    View para detalhes de categoria

    Princípios SOLID aplicados:
    - Single Responsibility: Apenas exibição de categoria
    - Open/Closed: Extensível para customizações
    """
    model = Category
    template_name = 'articles/category_detail.html'
    context_object_name = 'category'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_object(self, queryset=None) -> Category:
        """Obtém categoria"""
        try:
            return self.category_service.get_category_by_slug(self.kwargs['slug'])
        except Category.DoesNotExist:
            raise Http404("Categoria não encontrada")

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Adiciona artigos da categoria"""
        context = super().get_context_data(**kwargs)
        category = self.object

        context.update({
            'articles': self.category_service.get_category_articles(category),
            'meta_title': f'Categoria: {category.name}',
            'meta_description': category.description or f'Artigos da categoria {category.name}',
        })

        return context


class CategoryListView(BaseArticleView, ListView):
    """
    View para listagem de categorias

    Princípios SOLID aplicados:
    - Single Responsibility: Apenas listagem de categorias
    """
    model = Category
    template_name = 'articles/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self) -> QuerySet[Category]:
        """Retorna categorias com artigos"""
        return self.category_service.get_categories_with_articles()

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Adiciona dados específicos do contexto"""
        context = super().get_context_data(**kwargs)
        context.update({
            'meta_title': 'Categorias',
            'meta_description': 'Todas as categorias de artigos',
        })
        return context
        return redirect('articles:article_list')
