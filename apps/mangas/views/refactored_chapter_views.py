"""Views refatoradas para capítulos
Exemplo de como simplificar views complexas usando services dedicados"""

import logging
from django.views.generic import DetailView
from django.http import Http404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

from ..models.capitulo import Capitulo
from ..services.chapter_service import ChapterService
from ..exceptions import ChapterNotFoundError
from ..mixins.permission_mixins import ChapterOwnerOrStaffMixin

logger = logging.getLogger(__name__)

class RefactoredCapituloDetailView(DetailView):
    """
    View refatorada para detalhes do capítulo
    
    ANTES: 70+ linhas de lógica complexa
    DEPOIS: ~30 linhas usando service dedicado
    """
    model = Capitulo
    template_name = 'mangas/capitulo_detail.html'
    context_object_name = 'capitulo'
    slug_field = 'slug'
    slug_url_kwarg = 'capitulo_slug'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.chapter_service = ChapterService()
    
    def get_object(self, queryset=None):
        """Obtém capítulo usando service com tratamento de erros"""
        try:
            manga_slug = self.kwargs.get('manga_slug')
            chapter_slug = self.kwargs.get('capitulo_slug')
            
            return self.chapter_service.get_chapter_by_slug(
                manga_slug=manga_slug,
                chapter_slug=chapter_slug,
                user=self.request.user
            )
        except ChapterNotFoundError as e:
            logger.error(f"Capítulo não encontrado: {e}")
            raise Http404("Capítulo não encontrado")
    
    def get_context_data(self, **kwargs):
        """Contexto simplificado usando service"""
        context = super().get_context_data(**kwargs)
        
        try:
            # Obtém contexto completo do service
            page_number = self.request.GET.get('page', '1')
            chapter_context = self.chapter_service.get_complete_chapter_context(
                chapter=self.object,
                page_number=page_number,
                user=self.request.user
            )
            
            # Incrementa visualizações
            self.chapter_service.increment_chapter_views(self.object)
            
            # Adiciona ao contexto
            context.update(chapter_context)
            
        except Exception as e:
            logger.error(f"Erro ao obter contexto do capítulo: {e}")
            messages.error(self.request, "Erro ao carregar capítulo")
        
        return context

class RefactoredCapituloUpdateView(LoginRequiredMixin, ChapterOwnerOrStaffMixin, DetailView):
    """
    View refatorada para atualização de capítulo
    Exemplo de como usar services em outras operações
    """
    model = Capitulo
    template_name = 'mangas/capitulo_form.html'
    slug_field = 'slug'
    slug_url_kwarg = 'capitulo_slug'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.chapter_service = ChapterService()
    
    def get_object(self, queryset=None):
        """Obtém capítulo para edição"""
        try:
            manga_slug = self.kwargs.get('manga_slug')
            chapter_slug = self.kwargs.get('capitulo_slug')
            
            return self.chapter_service.get_chapter_by_slug(
                manga_slug=manga_slug,
                chapter_slug=chapter_slug,
                user=self.request.user
            )
        except ChapterNotFoundError:
            raise Http404("Capítulo não encontrado")

# Exemplo de como a view original poderia ser ainda mais simplificada
class MinimalCapituloDetailView(DetailView):
    """
    Versão minimalista da view de capítulo
    Demonstra o máximo de simplificação possível
    """
    model = Capitulo
    template_name = 'mangas/capitulo_detail.html'
    context_object_name = 'capitulo'
    slug_field = 'slug'
    slug_url_kwarg = 'capitulo_slug'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.chapter_service = ChapterService()
    
    def get_object(self, queryset=None):
        """Service handle object retrieval"""
        return self.chapter_service.get_chapter_by_slug(
            self.kwargs['manga_slug'],
            self.kwargs['capitulo_slug'],
            self.request.user
        )
    
    def get_context_data(self, **kwargs):
        """Service handles all context logic"""
        context = super().get_context_data(**kwargs)
        context.update(
            self.chapter_service.get_complete_chapter_context(
                self.object,
                self.request.GET.get('page', '1'),
                self.request.user
            )
        )
        self.chapter_service.increment_chapter_views(self.object)
        return context