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


class ArticleSlugMixin:
    """
    Mixin para obter artigos por slug
    
    Elimina duplicação de código entre views que precisam obter artigos por slug
    """
    def get_object(self, queryset=None) -> Article:
        """Obtém artigo por slug usando service"""
        try:
            return self.article_service.get_article_by_slug(self.kwargs['slug'])
        except Article.DoesNotExist:
            raise Http404("Artigo não encontrado")


class CategorySlugMixin:
    """
    Mixin para obter categorias por slug
    
    Elimina duplicação de código entre views que precisam obter categorias por slug
    """
    def get_object(self, queryset=None) -> Category:
        """Obtém categoria por slug usando service"""
        try:
            return self.category_service.get_category_by_slug(self.kwargs['slug'])
        except Category.DoesNotExist:
            raise Http404("Categoria não encontrada")


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
        """Retorna queryset de artigos com filtros e busca"""
        queryset = self.article_service.get_published_articles()
        
        # Filtro por categoria
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Busca por query
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(excerpt__icontains=search_query) |
                Q(content__icontains=search_query)
            )
        
        # Ordenação
        sort_by = self.request.GET.get('sort_by', 'newest')
        if sort_by == 'title':
            queryset = queryset.order_by('title')
        elif sort_by == 'oldest':
            queryset = queryset.order_by('published_at')
        elif sort_by == 'views':
            queryset = queryset.order_by('-view_count')
        elif sort_by == 'author':
            queryset = queryset.order_by('author__first_name', 'author__last_name')
        else:  # newest (default)
            queryset = queryset.order_by('-published_at')
        
        return queryset

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Adiciona dados específicos do contexto"""
        context = super().get_context_data(**kwargs)
        
        # Parâmetros de busca e filtro
        search_query = self.request.GET.get('q', '')
        category_slug = self.request.GET.get('category', '')
        sort_by = self.request.GET.get('sort_by', 'newest')
        
        # Adicionar ao contexto
        context['search_query'] = search_query
        context['current_category'] = category_slug
        context['sort_by'] = sort_by
        
        # Adicionar categorias
        context['categories'] = self.category_service.get_categories_with_articles()
        
        # Categoria atual para exibição
        if category_slug:
            try:
                context['category'] = self.category_service.get_category_by_slug(category_slug)
            except:
                context['category'] = None
        
        # Artigos em destaque apenas se não houver busca ou filtro
        if not search_query and not category_slug:
            context['featured_articles'] = self.article_service.get_featured_articles(limit=3)
        
        # Dados específicos da listagem
        context.update({
            'meta_title': 'Artigos',
            'meta_description': 'Todos os artigos do blog',
        })

        return context

class ArticleDetailView(ArticleSlugMixin, BaseArticleView, DetailView):
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
            # Comentários são gerenciados pelo sistema global (apps.comments)
            # Use as template tags {% load comments_tags %} nos templates
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
        search_param = self.request.GET.get('search', '').strip()  # Para compatibilidade com AJAX
        category = self.request.GET.get('category', '')
        tag = self.request.GET.get('tag', '')
        sort = self.request.GET.get('sort', '-published_at')

        # Usa 'search' se 'q' estiver vazio (compatibilidade AJAX)
        if not query and search_param:
            query = search_param

        # Inicia com artigos publicados
        queryset = self.article_service.get_published_articles()

        # Aplica busca por texto se houver query
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(excerpt__icontains=query) |
                Q(content__icontains=query) |
                Q(meta_keywords__icontains=query) |
                Q(tags__name__icontains=query)
            ).distinct()

        # Aplica filtro por categoria
        if category:
            queryset = queryset.filter(category__slug=category)

        # Aplica filtro por tag
        if tag:
            queryset = queryset.filter(tags__slug=tag)

        # Para requisições AJAX sem filtros, retorna todos os artigos publicados
        # Para requisições normais sem filtros, retorna queryset vazio (para não mostrar todos os artigos na página de busca)
        if not query and not category and not tag:
            is_ajax = self.request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            if not is_ajax:
                return Article.objects.none()

        # Aplica ordenação
        if sort:
            queryset = queryset.order_by(sort)

        return queryset

    def get(self, request, *args, **kwargs):
        """Override para detectar requisições AJAX e retornar JSON"""
        # Detecta se é uma requisição AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return self.get_ajax_response()
        
        # Para requisições normais, usa o comportamento padrão
        return super().get(request, *args, **kwargs)

    def get_ajax_response(self):
        """Retorna resposta JSON para requisições AJAX"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"AJAX Request - Page: {self.request.GET.get('page', 1)}, Params: {dict(self.request.GET)}")
            
            # Obtém os artigos paginados
            self.object_list = self.get_queryset()
            logger.info(f"QuerySet count: {self.object_list.count()}")
            
            # Usa uma abordagem mais segura para obter o contexto
            try:
                context = self.get_context_data(object_list=self.object_list)
                logger.info("Context data obtained successfully")
            except Exception as context_error:
                logger.error(f"Error in get_context_data: {str(context_error)}")
                # Fallback: criar contexto manualmente
                from django.core.paginator import Paginator
                paginator = Paginator(self.object_list, self.paginate_by)
                page_number = self.request.GET.get('page', 1)
                page_obj = paginator.get_page(page_number)
                
                context = {
                    'articles': page_obj,
                    'paginator': paginator,
                    'page_obj': page_obj,
                }
                logger.info("Fallback context created")
            
            # Prepara dados dos artigos para JSON
            articles_data = []
            try:
                for article in context['articles']:
                    # Formatar data de publicação
                    published_date = ''
                    if article.published_at:
                        published_date = article.published_at.strftime('%d/%m/%Y')
                    
                    # Calcular tempo de leitura (aproximado)
                    reading_time = 5  # valor padrão
                    if hasattr(article, 'content') and article.content:
                        word_count = len(article.content.split())
                        reading_time = max(1, word_count // 200)  # ~200 palavras por minuto
                    
                    article_data = {
                        'id': article.id,
                        'title': article.title,
                        'slug': article.slug,
                        'excerpt': article.excerpt or '',
                        'published_at': published_date,
                        'views': getattr(article, 'view_count', 0),
                        'reading_time': reading_time,
                        'url': article.get_absolute_url(),
                    }
                    
                    # Adiciona autor com verificação segura
                    if hasattr(article, 'author') and article.author:
                        article_data['author'] = article.author.get_full_name() or article.author.username
                    else:
                        article_data['author'] = 'Autor desconhecido'
                    
                    # Adiciona categoria como string simples
                    if hasattr(article, 'category') and article.category:
                        article_data['category'] = article.category.name
                    else:
                        article_data['category'] = 'Sem categoria'
                    
                    # Adiciona imagem com verificação segura
                    if hasattr(article, 'featured_image') and article.featured_image:
                        try:
                            article_data['featured_image'] = article.featured_image.url
                        except:
                            article_data['featured_image'] = None
                    else:
                        article_data['featured_image'] = None
                    
                    articles_data.append(article_data)
                    
                logger.info(f"Articles data prepared: {len(articles_data)} articles")
            except Exception as articles_error:
                logger.error(f"Error preparing articles data: {str(articles_error)}")
                raise articles_error
                
            # Prepara dados de paginação
            paginator = context.get('paginator')
            page_obj = context.get('page_obj')
            
            pagination_data = {
                'has_next': page_obj.has_next() if page_obj else False,
                'has_previous': page_obj.has_previous() if page_obj else False,
                'current_page': page_obj.number if page_obj else 1,
                'total_pages': paginator.num_pages if paginator else 1,
                'total_count': paginator.count if paginator else len(articles_data),
            }
            
            logger.info(f"Pagination data: {pagination_data}")
            
            response_data = {
                'success': True,
                'articles': articles_data,
                'pagination': pagination_data,
                'search_query': self.request.GET.get('q', ''),
                'filters': {
                    'category': self.request.GET.get('category', ''),
                    'tag': self.request.GET.get('tag', ''),
                    'sort': self.request.GET.get('sort', '-published_at'),
                }
            }
            
            logger.info("AJAX response prepared successfully")
            return JsonResponse(response_data)
            
        except Exception as e:
            logger.error(f"AJAX Error: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': f'Erro na busca: {str(e)}',
                'debug_info': {
                    'page': self.request.GET.get('page', 1),
                    'params': dict(self.request.GET)
                }
            }, status=500)

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Adiciona dados específicos da busca"""
        context = super().get_context_data(**kwargs)

        query = self.request.GET.get('q', '').strip()
        search_param = self.request.GET.get('search', '').strip()
        
        # Usa 'search' se 'q' estiver vazio
        if not query and search_param:
            query = search_param
            
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


class ArticleUpdateView(ArticleSlugMixin, EditorOrAdminRequiredMixin, BaseArticleView, UpdateView):
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


class ArticleDeleteView(ArticleSlugMixin, EditorOrAdminRequiredMixin, BaseArticleView, DeleteView):
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


class CategoryDetailView(CategorySlugMixin, BaseArticleView, DetailView):
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
