from django.shortcuts import render
from django.views import View
from django.http import Http404
from apps.pages.services.page_service import PageService
from apps.pages.repositories.page_repository import DjangoPageRepository
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from apps.articles.repositories.article_repository import DjangoArticleRepository

class HomeView(View):
    """View para a página inicial"""
    
    def get(self, request):
        """Exibe a página inicial"""
        setup_completed = request.session.pop('setup_completed', False)
        page_service = PageService(DjangoPageRepository())
        article_repository = DjangoArticleRepository()
        try:
            homepage = page_service.get_homepage()
            main_articles = article_repository.list_published(limit=6)
            # Se houver homepage, usa seus metadados; senão, usa padrão
            context = {
                'page': homepage,
                'is_homepage': True,
                'main_articles': main_articles,
                'meta_title': homepage.seo_title if homepage else 'Bem-vindo ao FireFlies',
                'meta_description': homepage.seo_description if homepage else 'Sistema de gerenciamento de conteúdo moderno com arquitetura limpa',
                'meta_keywords': homepage.meta_keywords if homepage else '',
                'setup_completed': setup_completed,
            }
            return render(request, 'pages/home.html', context)
        except Exception as e:
            context = {
                'page': None,
                'is_homepage': True,
                'error': str(e),
                'meta_title': 'FireFlies - Sistema de Gerenciamento',
                'meta_description': 'Sistema de gerenciamento de conteúdo',
                'main_articles': [],
                'setup_completed': setup_completed,
            }
            return render(request, 'pages/home.html', context)
