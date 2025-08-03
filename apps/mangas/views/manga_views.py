import logging
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import Http404
from django.db import models
from django.db.models import Q

from apps.mangas.models.manga import Manga
from apps.mangas.models.volume import Volume
from apps.mangas.models.capitulo import Capitulo
from apps.mangas.models.pagina import Pagina
from apps.mangas.forms.manga_form import MangaForm, CapituloForm, CapituloCompleteForm, PaginaForm
from apps.mangas.services.file_processor_service import MangaFileProcessorService
from apps.mangas.mixins.permission_mixins import (
    StaffOrSuperuserRequiredMixin,
    MangaOwnerOrStaffMixin,
    ChapterOwnerOrStaffMixin,
    PageOwnerOrStaffMixin
)

logger = logging.getLogger(__name__)

# Mangá
class MangaListView(ListView):
    model = Manga
    template_name = 'mangas/manga_list.html'
    context_object_name = 'mangas'
    paginate_by = 12

    def get_queryset(self):
        queryset = Manga.objects.filter(is_published=True)
        
        # Busca por query
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(author__icontains=search_query)
            )
        
        # Ordenação
        sort_by = self.request.GET.get('sort_by', 'newest')
        if sort_by == 'title':
            queryset = queryset.order_by('title')
        elif sort_by == 'oldest':
            queryset = queryset.order_by('created_at')
        elif sort_by == 'views':
            queryset = queryset.order_by('-view_count')
        elif sort_by == 'author':
            queryset = queryset.order_by('author')
        else:  # newest (default)
            queryset = queryset.order_by('-created_at')
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Parâmetros de busca e filtro
        search_query = self.request.GET.get('q', '')
        sort_by = self.request.GET.get('sort_by', 'newest')
        
        # Adicionar ao contexto
        context['search_query'] = search_query
        context['sort_by'] = sort_by
        
        return context

class MangaDetailView(DetailView):
    """
    Exibe os detalhes de um mangá específico - REFATORADA para usar Service Layer
    """
    model = Manga
    template_name = 'mangas/manga_detail.html'
    context_object_name = 'manga'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    paginate_by = 10  # Número de volumes por página

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Injeção de dependência do service
        from ..services.manga_service_simple import SimpleMangaService
        self.manga_service = SimpleMangaService()

    def get_object(self, queryset=None):
        """Usa service para obter o mangá com otimizações"""
        slug = self.kwargs.get(self.slug_url_kwarg)
        try:
            return self.manga_service.get_manga_by_slug(slug)
        except Exception as e:
            logger.error(f"Erro ao buscar manga {slug}: {e}")
            raise Http404("Mangá não encontrado")

    def get_context_data(self, **kwargs):
        """Adiciona contexto usando Service Layer - REFATORADO"""
        context = super().get_context_data(**kwargs)

        # Usa service para obter contexto do mangá
        manga_context = self.manga_service.get_manga_context(self.object)

        # Configura paginação dos volumes
        volumes = manga_context.get('volumes', [])
        paginator = Paginator(volumes, self.paginate_by)
        page = self.request.GET.get('page')

        try:
            volumes_paginados = paginator.page(page)
        except PageNotAnInteger:
            volumes_paginados = paginator.page(1)
        except EmptyPage:
            volumes_paginados = paginator.page(paginator.num_pages)

        # Incrementa visualizações do mangá
        try:
            self.manga_service.increment_manga_views(self.object.id)
        except Exception as e:
            logger.warning(f"Erro ao incrementar views: {e}")

        # Adiciona contexto do service
        context.update({
            'volumes': volumes_paginados,
            'total_chapters': manga_context.get('total_chapters', 0),
            'latest_chapter': manga_context.get('latest_chapter'),
            'chapter_count': manga_context.get('chapter_count', 0),
        })

        return context

class MangaCreateView(LoginRequiredMixin, StaffOrSuperuserRequiredMixin, CreateView):
    """
    View para criar um novo mangá.
    Apenas membros da equipe ou superusuários podem acessar.
    """
    model = Manga
    form_class = MangaForm
    template_name = 'mangas/manga_form.html'
    success_url = reverse_lazy('mangas:manga_list')
    
    def form_valid(self, form):
        """Define o usuário atual como criador do mangá."""
        form.instance.criado_por = self.request.user
        messages.success(self.request, 'Mangá criado com sucesso!')
        return super().form_valid(form)

class MangaUpdateView(LoginRequiredMixin, MangaOwnerOrStaffMixin, UpdateView):
    """
    View para atualizar um mangá existente.
    Apenas o criador do mangá, membros da equipe ou superusuários podem acessar.
    """
    model = Manga
    form_class = MangaForm
    template_name = 'mangas/manga_form.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    success_url = reverse_lazy('mangas:manga_list')
    
    def form_valid(self, form):
        """Exibe mensagem de sucesso ao atualizar o mangá."""
        messages.success(self.request, 'Mangá atualizado com sucesso!')
        return super().form_valid(form)

class MangaDeleteView(LoginRequiredMixin, MangaOwnerOrStaffMixin, DeleteView):
    """
    View para excluir um mangá existente.
    Apenas o criador do mangá, membros da equipe ou superusuários podem acessar.
    """
    model = Manga
    template_name = 'mangas/manga_confirm_delete.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    success_url = reverse_lazy('mangas:manga_list')
    
    def delete(self, request, *args, **kwargs):
        """Exibe mensagem de sucesso ao excluir o mangá."""
        messages.success(request, 'Mangá excluído com sucesso!')
        return super().delete(request, *args, **kwargs)

class CapituloDetailView(DetailView):
    """
    Exibe os detalhes de um capítulo - REFATORADA para usar Service Layer
    """
    model = Capitulo
    template_name = 'mangas/capitulo_detail.html'
    context_object_name = 'capitulo'
    slug_field = 'slug'
    slug_url_kwarg = 'capitulo_slug'
    paginate_by = 1  # Uma página por vez (leitor de mangá)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Injeção de dependência do service
        from ..services.manga_service_simple import SimpleMangaService
        self.manga_service = SimpleMangaService()

    def get_queryset(self):
        """Otimiza a consulta ao banco de dados."""
        # Filtra capítulos publicados para usuários não autenticados ou sem permissões
        if not self.request.user.is_authenticated or not self.request.user.is_staff:
            return Capitulo.objects.filter(is_published=True).select_related('volume__manga').prefetch_related('paginas')
        else:
            return Capitulo.objects.select_related('volume__manga').prefetch_related('paginas')
    
    def get_context_data(self, **kwargs):
        """Adiciona contexto usando Service Layer - REFATORADO"""
        context = super().get_context_data(**kwargs)

        # Obtém o capítulo do contexto
        capitulo = context['capitulo']

        # Usa service para obter contexto de navegação
        chapter_context = self.manga_service.get_chapter_context(capitulo)

        # Configura paginação das páginas
        paginas = chapter_context.get('pages', [])
        paginator = Paginator(paginas, self.paginate_by)
        page = self.request.GET.get('page')

        try:
            paginas_paginadas = paginator.page(page)
        except PageNotAnInteger:
            paginas_paginadas = paginator.page(1)
        except EmptyPage:
            paginas_paginadas = paginator.page(paginator.num_pages)

        # Incrementa visualizações do capítulo
        try:
            self.manga_service.increment_manga_views(capitulo.volume.manga.id)
        except Exception as e:
            logger.warning(f"Erro ao incrementar views: {e}")

        # Adiciona informações ao contexto
        context.update({
            'paginas': paginas_paginadas,
            'total_paginas': chapter_context.get('total_pages', 0),
            'current_page_number': paginas_paginadas.number,
            'has_previous': paginas_paginadas.has_previous(),
            'has_next': paginas_paginadas.has_next(),
            'previous_page_number': paginas_paginadas.previous_page_number() if paginas_paginadas.has_previous() else None,
            'next_page_number': paginas_paginadas.next_page_number() if paginas_paginadas.has_next() else None,
            'capitulo_anterior': chapter_context.get('previous_chapter'),
            'proximo_capitulo': chapter_context.get('next_chapter'),
            'volumes': capitulo.volume.manga.volumes.all().order_by('number'),
        })

        return context

class CapituloCreateView(LoginRequiredMixin, StaffOrSuperuserRequiredMixin, CreateView):
    """
    View para criar um novo capítulo.
    Apenas membros da equipe ou superusuários podem acessar.
    """
    model = Capitulo
    form_class = CapituloForm
    template_name = 'mangas/capitulo_form.html'
    
    def get_initial(self):
        """Define valores iniciais para o formulário."""
        return {
            'manga': self.kwargs.get('manga_slug')
        }
    
    def form_valid(self, form):
        """Define o volume relacionado ao capítulo."""
        volume_id = self.request.GET.get('volume')
        if not volume_id:
            messages.error(self.request, 'Volume não especificado.')
            return self.form_invalid(form)
        
        try:
            volume = Volume.objects.get(
                id=volume_id,
                manga__slug=self.kwargs['manga_slug']
            )
            form.instance.volume = volume
            messages.success(self.request, 'Capítulo criado com sucesso!')
            return super().form_valid(form)
        except Volume.DoesNotExist:
            messages.error(self.request, 'Volume não encontrado.')
            return self.form_invalid(form)
    
    def get_success_url(self):
        """Retorna a URL de sucesso."""
        return reverse_lazy('mangas:manga_detail', kwargs={'slug': self.kwargs['manga_slug']})

class CapituloUpdateView(LoginRequiredMixin, ChapterOwnerOrStaffMixin, UpdateView):
    """
    View para atualizar um capítulo existente.
    Apenas o criador do mangá relacionado, membros da equipe ou superusuários podem acessar.
    """
    model = Capitulo
    form_class = CapituloForm
    template_name = 'mangas/capitulo_form.html'
    slug_field = 'slug'
    slug_url_kwarg = 'capitulo_slug'
    
    def get_queryset(self):
        """Filtra o queryset para o mangá específico."""
        return Capitulo.objects.filter(volume__manga__slug=self.kwargs['manga_slug'])
    
    def form_valid(self, form):
        """Exibe mensagem de sucesso ao atualizar o capítulo."""
        messages.success(self.request, 'Capítulo atualizado com sucesso!')
        return super().form_valid(form)
    
    def get_success_url(self):
        """Retorna a URL de sucesso."""
        return reverse_lazy('mangas:manga_detail', kwargs={'slug': self.kwargs['manga_slug']})

class CapituloDeleteView(LoginRequiredMixin, ChapterOwnerOrStaffMixin, DeleteView):
    """
    View para excluir um capítulo existente.
    Apenas o criador do mangá relacionado, membros da equipe ou superusuários podem acessar.
    """
    model = Capitulo
    template_name = 'mangas/capitulo_confirm_delete.html'
    slug_field = 'slug'
    slug_url_kwarg = 'capitulo_slug'
    
    def get_queryset(self):
        """Filtra o queryset para o mangá específico."""
        return Capitulo.objects.filter(volume__manga__slug=self.kwargs['manga_slug'])
    
    def delete(self, request, *args, **kwargs):
        """Exibe mensagem de sucesso ao excluir o capítulo."""
        messages.success(request, 'Capítulo excluído com sucesso!')
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        """Retorna a URL de sucesso."""
        return reverse_lazy('mangas:manga_detail', kwargs={'slug': self.kwargs['manga_slug']})

class PaginaCreateView(LoginRequiredMixin, StaffOrSuperuserRequiredMixin, CreateView):
    """
    View para criar uma nova página.
    Apenas membros da equipe ou superusuários podem acessar.
    """
    model = Pagina
    form_class = PaginaForm
    template_name = 'mangas/pagina_form.html'
    
    def get_initial(self):
        """Define valores iniciais para o formulário."""
        return {
            'capitulo': self.kwargs.get('capitulo_slug')
        }
    
    def form_valid(self, form):
        """Define o capítulo relacionado à página."""
        form.instance.capitulo = Capitulo.objects.get(
            volume__manga__slug=self.kwargs['manga_slug'],
            slug=self.kwargs['capitulo_slug']
        )
        messages.success(self.request, 'Página criada com sucesso!')
        return super().form_valid(form)
    
    def get_success_url(self):
        """Retorna a URL de sucesso."""
        return reverse_lazy('mangas:capitulo_detail', kwargs={
            'manga_slug': self.kwargs['manga_slug'],
            'capitulo_slug': self.kwargs['capitulo_slug']
        })

class PaginaUpdateView(LoginRequiredMixin, PageOwnerOrStaffMixin, UpdateView):
    """
    View para atualizar uma página existente.
    Apenas o criador do mangá relacionado, membros da equipe ou superusuários podem acessar.
    """
    model = Pagina
    form_class = PaginaForm
    template_name = 'mangas/pagina_form.html'
    
    def get_queryset(self):
        """Filtra o queryset para o capítulo específico."""
        return Pagina.objects.filter(
            capitulo__volume__manga__slug=self.kwargs['manga_slug'],
            capitulo__slug=self.kwargs['capitulo_slug']
        )
    
    def form_valid(self, form):
        """Exibe mensagem de sucesso ao atualizar a página."""
        messages.success(self.request, 'Página atualizada com sucesso!')
        return super().form_valid(form)
    
    def get_success_url(self):
        """Retorna a URL de sucesso."""
        return reverse_lazy('mangas:capitulo_detail', kwargs={
            'manga_slug': self.kwargs['manga_slug'],
            'capitulo_slug': self.kwargs['capitulo_slug']
        })

class PaginaDeleteView(LoginRequiredMixin, PageOwnerOrStaffMixin, DeleteView):
    """
    View para excluir uma página existente.
    Apenas o criador do mangá relacionado, membros da equipe ou superusuários podem acessar.
    """
    model = Pagina
    template_name = 'mangas/pagina_confirm_delete.html'
    
    def get_queryset(self):
        """Filtra o queryset para o capítulo específico."""
        return Pagina.objects.filter(
            capitulo__volume__manga__slug=self.kwargs['manga_slug'],
            capitulo__slug=self.kwargs['capitulo_slug']
        )
    
    def delete(self, request, *args, **kwargs):
        """Exibe mensagem de sucesso ao excluir a página."""
        messages.success(request, 'Página excluída com sucesso!')
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        """Retorna a URL de sucesso."""
        return reverse_lazy('mangas:capitulo_detail', kwargs={
            'manga_slug': self.kwargs['manga_slug'],
            'capitulo_slug': self.kwargs['capitulo_slug']
        })

class CapituloCompleteCreateView(LoginRequiredMixin, StaffOrSuperuserRequiredMixin, CreateView):
    """
    View para criação de capítulo completo com upload de arquivo compactado.
    
    Permite o upload de um arquivo .zip, .rar, .cbz, .cbr ou .pdf contendo as páginas
    do capítulo, que serão extraídas e salvas automaticamente.
    """
    model = Capitulo
    form_class = CapituloCompleteForm
    template_name = 'mangas/capitulo_complete_form.html'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_processor = MangaFileProcessorService()
    
    def get_initial(self):
        """Define valores iniciais para o formulário."""
        return {
            'manga': self.kwargs.get('manga_slug')
        }
    
    def get_context_data(self, **kwargs):
        """Adiciona o mangá ao contexto."""
        context = super().get_context_data(**kwargs)
        context['manga'] = Manga.objects.get(slug=self.kwargs['manga_slug'])
        return context
    
    def form_valid(self, form):
        """Processa o upload do arquivo e cria o capítulo com páginas."""
        try:
            # Obtém o volume do parâmetro da URL
            volume_id = self.request.GET.get('volume')
            if not volume_id:
                messages.error(self.request, 'Volume não especificado.')
                return self.form_invalid(form)
            
            try:
                volume = Volume.objects.get(
                    id=volume_id,
                    manga__slug=self.kwargs['manga_slug']
                )
            except Volume.DoesNotExist:
                messages.error(self.request, 'Volume não encontrado.')
                return self.form_invalid(form)
            
            # Salva o capítulo primeiro
            capitulo = form.save(commit=False)
            capitulo.volume = volume
            capitulo.save()
            
            # Processa o arquivo se foi fornecido
            arquivo = form.cleaned_data.get('arquivo_capitulo')
            
            if arquivo:
                success, message = self.file_processor.process_chapter_file(capitulo, arquivo)
                if not success:
                    messages.error(self.request, f'Erro ao processar arquivo: {message}')
                    capitulo.delete()  # Remove o capítulo se falhar
                    return self.form_invalid(form)
            else:
                messages.error(self.request, 'Nenhum arquivo enviado. Verifique o tipo de codificação do formulário.')
                capitulo.delete()  # Remove o capítulo se não há arquivo
                return self.form_invalid(form)
            
            messages.success(self.request, 'Capítulo criado com sucesso!')
            return super().form_valid(form)
            
        except Exception as e:
            logger.error(f'Erro ao criar capítulo completo: {str(e)}', exc_info=True)
            messages.error(self.request, f'Erro ao criar capítulo: {str(e)}')
            return self.form_invalid(form)
    
    def get_success_url(self):
        """Retorna a URL de sucesso."""
        return reverse_lazy('mangas:manga_detail', kwargs={'slug': self.kwargs['manga_slug']})