from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
import logging

from apps.mangas.models import Manga
from apps.mangas.forms.unified_forms import UnifiedMangaForm
from apps.mangas.services.unified_manga_service import unified_manga_service
from apps.mangas.mixins.permission_mixins import StaffOrSuperuserRequiredMixin

logger = logging.getLogger(__name__)

class UnifiedMangaListView(ListView):
    """View unificada para listagem de mangás."""
    model = Manga
    template_name = 'mangas/manga_list.html'
    context_object_name = 'mangas'
    paginate_by = 20
    
    def get_queryset(self):
        return Manga.objects.filter(is_published=True).order_by('-created_at')

class UnifiedMangaDetailView(DetailView):
    """View unificada para detalhes do mangá - CORRIGIDA para usar slug."""
    model = Manga
    template_name = 'mangas/manga_detail.html'
    context_object_name = 'manga'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_object(self, queryset=None):
        slug = self.kwargs.get('slug')
        manga = unified_manga_service.get_manga_by_slug_with_cache(slug)
        
        if not manga:
            from django.http import Http404
            raise Http404("Mangá não encontrado")
        
        return manga
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = unified_manga_service.get_manga_stats(self.object)
        return context

@method_decorator(login_required, name='dispatch')
class UnifiedMangaCreateView(LoginRequiredMixin, StaffOrSuperuserRequiredMixin, CreateView):
    """View unificada para criação de mangás - CORRIGIDA."""
    model = Manga
    form_class = UnifiedMangaForm
    template_name = 'mangas/manga_form.html'
    
    def get_success_url(self):
        return reverse_lazy('mangas:unified_detail', kwargs={'slug': self.object.slug})
    
    def form_valid(self, form):
        try:
            data = form.cleaned_data.copy()
            cover_image = data.pop('cover_image', None)
            
            manga = unified_manga_service.create_manga(data, cover_image)
            self.object = manga
            
            messages.success(
                self.request,
                f'Mangá "{manga.title}" criado com sucesso!'
            )
            
            return redirect(self.get_success_url())
            
        except Exception as e:
            logger.error(f"Erro ao criar mangá: {str(e)}")
            messages.error(
                self.request,
                f'Erro ao criar mangá: {str(e)}'
            )
            return self.form_invalid(form)

def manga_stats_api(request, slug):
    """API para estatísticas do mangá - CORRIGIDA para usar slug."""
    try:
        manga = unified_manga_service.get_manga_by_slug_with_cache(slug)
        if not manga:
            return JsonResponse({'error': 'Mangá não encontrado'}, status=404)
        
        stats = unified_manga_service.get_manga_stats(manga)
        
        return JsonResponse({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Erro na API de stats: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)