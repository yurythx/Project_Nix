from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from apps.articles.services.article_service import ArticleService
from apps.articles.repositories.article_repository import DjangoArticleRepository
from apps.articles.interfaces.services import IArticleService
from apps.articles.models.article import Article
from apps.articles.models.category import Category
from apps.articles.models.tag import Tag
from apps.articles.forms import ArticleForm
from core.factories import service_factory
from apps.common.mixins import ModuleEnabledRequiredMixin

class ArticleListView(ModuleEnabledRequiredMixin, ListView):
    module_name = 'apps.articles'
    model = Article
    template_name = 'articles/article_list.html'
    context_object_name = 'articles'
    paginate_by = 12

    def get_queryset(self):
        service = service_factory.create_article_service()
        return service.get_published_articles()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = service_factory.create_article_service()
        context['featured_articles'] = service.get_featured_articles(limit=3)
        context['categories'] = Category.objects.filter(articles__isnull=False).distinct().order_by('name')
        context['meta_title'] = 'Artigos'
        context['meta_description'] = 'Todos os artigos do blog'
        return context

class ArticleDetailView(ModuleEnabledRequiredMixin, DetailView):
    module_name = 'apps.articles'
    model = Article
    template_name = 'articles/article_detail.html'
    context_object_name = 'article'
    slug_field = 'slug'
    slug_url_arg = 'slug'

    def get_object(self, queryset=None):
        service = service_factory.create_article_service()
        return service.get_article_by_slug(self.kwargs['slug'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = service_factory.create_article_service()
        article = self.object
        service.increment_article_views(article.id)
        context['related_articles'] = service.get_related_articles(article, limit=3)
        context['comments'] = article.comments.filter(is_approved=True, parent__isnull=True).order_by('-created_at')[:5]
        context['comment_count'] = article.comments.filter(is_approved=True).count()
        context['meta_title'] = article.seo_title or article.title
        context['meta_description'] = article.seo_description or article.excerpt
        context['meta_keywords'] = getattr(article, 'meta_keywords', '') or ''
        return context


def test_article_view(request, slug):
    """View de teste simples"""
    from django.http import HttpResponse
    from apps.articles.models.article import Article

    try:
        article = Article.objects.get(slug=slug, status='published')
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{article.title}</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
                .meta {{ color: #666; margin-bottom: 20px; }}
                .content {{ line-height: 1.6; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{article.title}</h1>
                <div class="meta">
                    <p><strong>Autor:</strong> {article.author.username}</p>
                    <p><strong>Categoria:</strong> {article.category.name if article.category else 'Sem categoria'}</p>
                    <p><strong>Publicado em:</strong> {article.published_at}</p>
                    <p><strong>Visualizações:</strong> {article.view_count}</p>
                </div>
                <div class="content">
                    <h2>Conteúdo:</h2>
                    <div>{article.content}</div>
                </div>
                <hr>
                <h2>🎯 Sistema de Comentários Funcionando!</h2>
                <p>✅ View de teste funcionando corretamente</p>
                <p>✅ Artigo carregado com sucesso</p>
                <p>✅ Dados do artigo acessíveis</p>

                <h3>Links de teste:</h3>
                <ul>
                    <li><a href="/artigos/{article.slug}/">View original</a></li>
                    <li><a href="/artigos/">Lista de artigos</a></li>
                    <li><a href="/artigos/{article.slug}/comentarios/">Lista de comentários</a></li>
                </ul>
            </div>
        </body>
        </html>
        """
        return HttpResponse(html)
    except Article.DoesNotExist:
        return HttpResponse(f"<h1>Artigo '{slug}' não encontrado</h1>", status=404)
    except Exception as e:
        return HttpResponse(f"<h1>Erro: {e}</h1>", status=500)


class ArticleSearchView(View):
    """View para busca de artigos"""
    template_name = 'articles/search_results.html'
    
    def __init__(self, article_service=None):
        super().__init__()
        self.article_service = article_service or service_factory.create_article_service()
    
    def get(self, request):
        """Busca artigos"""
        query = request.GET.get('q', '').strip()
        
        if not query:
            context = {
                'query': '',
                'articles': [],
                'total_results': 0,
                'meta_title': 'Busca de Artigos',
                'meta_description': 'Busque por artigos no blog',
            }
            return render(request, self.template_name, context)
        
        # Busca artigos usando o service injetado
        articles = self.article_service.search_articles(query)
        
        # Paginação
        paginator = Paginator(articles, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'query': query,
            'page_obj': page_obj,
            'articles': page_obj.object_list,
            'total_results': paginator.count,
            'meta_title': f'Busca por "{query}"',
            'meta_description': f'Resultados da busca por "{query}"',
        }
        
        return render(request, self.template_name, context)


class EditorOrAdminRequiredMixin(UserPassesTestMixin):
    """Permite acesso para admin, staff ou grupo 'Editor'"""
    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser or user.is_staff:
            return True
        if user.groups.filter(name__iexact='administrador').exists():
            return True
        if user.groups.filter(name__iexact='admin').exists():
            return True
        if user.groups.filter(name__iexact='editor').exists():
            return True
        return False
    def handle_no_permission(self):
        messages.error(self.request, '🚫 Acesso negado! Apenas administradores ou editores podem realizar esta ação.')
        return redirect('articles:article_list')


class ArticleCreateView(EditorOrAdminRequiredMixin, CreateView):
    """View para criar novos artigos"""
    model = Article
    form_class = ArticleForm
    template_name = 'articles/article_form.html'
    success_url = reverse_lazy('articles:article_list')
    
    def form_valid(self, form):
        print('DEBUG: Entrou no form_valid da ArticleCreateView')
        form.instance.author = self.request.user
        article = form.save()
        print(f'DEBUG: Artigo salvo? ID: {getattr(article, "id", None)} | Slug: {getattr(article, "slug", None)}')
        messages.success(self.request, '✅ Artigo criado com sucesso!')
        return redirect('articles:article_detail', slug=article.slug)
    
    def get_context_data(self, **kwargs):
        """Adiciona dados extras ao contexto"""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Criar Novo Artigo'
        context['button_text'] = 'Criar Artigo'
        return context


class ArticleUpdateView(EditorOrAdminRequiredMixin, UpdateView):
    """View para editar artigos"""
    model = Article
    form_class = ArticleForm
    template_name = 'articles/article_form.html'
    
    def __init__(self, article_service=None):
        super().__init__()
        self.article_service = article_service or service_factory.create_article_service()
    
    def form_valid(self, form):
        """Processa formulário válido"""
        data = form.cleaned_data.copy()
        data.pop('is_published', None)  # Remove o campo que não existe no model
        # Usa o service injetado para atualizar o artigo
        success = self.article_service.update_article(self.get_object().id, data, self.request.user)
        
        if success:
            messages.success(self.request, '✅ Artigo atualizado com sucesso!')
            return redirect('articles:article_detail', slug=form.instance.slug)
        else:
            messages.error(self.request, '❌ Ocorreu um erro ao atualizar o artigo. Tente novamente.')
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        """Adiciona dados extras ao contexto"""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Artigo'
        context['button_text'] = 'Atualizar Artigo'
        return context


class ArticleDeleteView(EditorOrAdminRequiredMixin, DeleteView):
    """View para deletar artigos"""
    model = Article
    template_name = 'articles/article_confirm_delete.html'
    success_url = reverse_lazy('articles:article_list')
    
    def __init__(self, article_service=None):
        super().__init__()
        self.article_service = article_service or service_factory.create_article_service()
    
    def delete(self, request, *args, **kwargs):
        """Processa exclusão"""
        article = self.get_object()
        
        # Usa o service injetado para deletar o artigo
        success = self.article_service.delete_article(article.id, request.user)
        
        if success:
            messages.success(request, '🗑️ Artigo removido com sucesso!')
        else:
            messages.error(request, '❌ Ocorreu um erro ao remover o artigo. Tente novamente.')
        
        return redirect(self.success_url)
    
    def get_context_data(self, **kwargs):
        """Adiciona dados extras ao contexto"""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Confirmar Exclusão'
        return context

class CategoryDetailView(ListView):
    model = Article
    template_name = 'articles/article_list.html'
    context_object_name = 'articles'
    paginate_by = 12

    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'], is_active=True)
        return Article.objects.filter(category=self.category, status='published').order_by('-published_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['categories'] = Category.objects.filter(articles__isnull=False).distinct().order_by('name')
        context['meta_title'] = f'Artigos em {self.category.name}'
        context['meta_description'] = self.category.seo_description
        context['featured_articles'] = Article.objects.filter(is_featured=True, status='published')[:3]
        return context

class CategoryListView(ListView):
    model = Category
    template_name = 'articles/category_list.html'
    context_object_name = 'categories'
    queryset = Category.objects.filter(is_active=True).order_by('name')
