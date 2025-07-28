import logging
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import Http404

from apps.mangas.models.manga import Manga
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
        queryset = super().get_queryset()
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(title__icontains=q)
        return queryset

class MangaDetailView(DetailView):
    """
    Exibe os detalhes de um mangá específico, incluindo uma lista paginada de capítulos.
    """
    model = Manga
    template_name = 'mangas/manga_detail.html'
    context_object_name = 'manga'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    paginate_by = 10  # Número de capítulos por página
    
    def get_context_data(self, **kwargs):
        """Adiciona a lista paginada de capítulos ao contexto."""
        context = super().get_context_data(**kwargs)
        
        # Obtém todos os capítulos ordenados por número (decrescente)
        capitulos = self.object.capitulos.all().order_by('-number')
        
        # Configura a paginação
        paginator = Paginator(capitulos, self.paginate_by)
        page = self.request.GET.get('page')
        
        try:
            capitulos_paginados = paginator.page(page)
        except PageNotAnInteger:
            # Se a página não for um inteiro, exibe a primeira página
            capitulos_paginados = paginator.page(1)
        except EmptyPage:
            # Se a página estiver fora do alcance (ex. 9999), exibe a última página
            capitulos_paginados = paginator.page(paginator.num_pages)
            
        context['capitulos'] = capitulos_paginados
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

# Capítulo
class CapituloDetailView(DetailView):
    """
    Exibe os detalhes de um capítulo, incluindo uma lista paginada de páginas.
    """
    model = Capitulo
    template_name = 'mangas/capitulo_detail.html'
    context_object_name = 'capitulo'
    slug_field = 'slug'
    slug_url_kwarg = 'capitulo_slug'
    paginate_by = 1  # Uma página por vez (leitor de mangá)
    
    def get_queryset(self):
        manga_slug = self.kwargs.get('manga_slug')
        return Capitulo.objects.filter(manga__slug=manga_slug)
    
    def get_context_data(self, **kwargs):
        """Adiciona a lista paginada de páginas ao contexto."""
        context = super().get_context_data(**kwargs)
        
        # Obtém todas as páginas ordenadas por número
        paginas = self.object.paginas.all().order_by('number')
        
        # Configura a paginação
        paginator = Paginator(paginas, self.paginate_by)
        page = self.request.GET.get('page')
        
        try:
            paginas_paginadas = paginator.page(page)
        except PageNotAnInteger:
            # Se a página não for um inteiro, exibe a primeira página
            paginas_paginadas = paginator.page(1)
        except EmptyPage:
            # Se a página estiver fora do alcance (ex. 9999), exibe a última página
            paginas_paginadas = paginator.page(paginator.num_pages)
            
        context['paginas'] = paginas_paginadas
        
        # Adiciona informações de navegação entre capítulos
        capitulo = self.get_object()
        context['capitulo_anterior'] = (
            Capitulo.objects
            .filter(manga=capitulo.manga, number__lt=capitulo.number)
            .order_by('-number')
            .first()
        )
        context['proximo_capitulo'] = (
            Capitulo.objects
            .filter(manga=capitulo.manga, number__gt=capitulo.number)
            .order_by('number')
            .first()
        )
        
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
        """Define o mangá relacionado ao capítulo."""
        self.manga = Manga.objects.get(slug=self.kwargs['manga_slug'])
        return {'manga': self.manga}
    
    def form_valid(self, form):
        """Define o mangá e o criador do capítulo."""
        form.instance.manga = self.manga
        form.instance.criado_por = self.request.user
        messages.success(self.request, 'Capítulo criado com sucesso!')
        return super().form_valid(form)
    
    def get_success_url(self):
        """Redireciona para a página do mangá após a criação do capítulo."""
        return self.object.manga.get_absolute_url()

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
        """Filtra os capítulos pelo mangá relacionado."""
        manga_slug = self.kwargs.get('manga_slug')
        return Capitulo.objects.filter(manga__slug=manga_slug)
    
    def form_valid(self, form):
        """Exibe mensagem de sucesso ao atualizar o capítulo."""
        messages.success(self.request, 'Capítulo atualizado com sucesso!')
        return super().form_valid(form)
    
    def get_success_url(self):
        """Redireciona para a página do mangá após a atualização do capítulo."""
        return self.object.manga.get_absolute_url()

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
        """Filtra os capítulos pelo mangá relacionado."""
        manga_slug = self.kwargs.get('manga_slug')
        return Capitulo.objects.filter(manga__slug=manga_slug)
    
    def delete(self, request, *args, **kwargs):
        """Exibe mensagem de sucesso ao excluir o capítulo."""
        messages.success(request, 'Capítulo excluído com sucesso!')
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        """Redireciona para a página do mangá após a exclusão do capítulo."""
        return self.object.manga.get_absolute_url()

# Página
class PaginaCreateView(LoginRequiredMixin, PageOwnerOrStaffMixin, CreateView):
    """
    View para criar uma nova página.
    Apenas o criador do mangá relacionado, membros da equipe ou superusuários podem acessar.
    """
    model = Pagina
    form_class = PaginaForm
    template_name = 'mangas/pagina_form.html'
    
    def get_initial(self):
        """Define o capítulo relacionado à página."""
        self.capitulo = Capitulo.objects.get(slug=self.kwargs['capitulo_slug'])
        return {'capitulo': self.capitulo}
    
    def form_valid(self, form):
        """Define o capítulo e o criador da página."""
        form.instance.capitulo = self.capitulo
        form.instance.criado_por = self.request.user
        messages.success(self.request, 'Página adicionada com sucesso!')
        return super().form_valid(form)
    
    def get_success_url(self):
        """Redireciona para a página do capítulo após a criação da página."""
        return self.object.capitulo.get_absolute_url()

class PaginaUpdateView(LoginRequiredMixin, PageOwnerOrStaffMixin, UpdateView):
    """
    View para atualizar uma página existente.
    Apenas o criador do mangá relacionado, membros da equipe ou superusuários podem acessar.
    """
    model = Pagina
    form_class = PaginaForm
    template_name = 'mangas/pagina_form.html'
    
    def get_queryset(self):
        """Filtra as páginas pelo capítulo relacionado."""
        capitulo_slug = self.kwargs.get('capitulo_slug')
        return Pagina.objects.filter(capitulo__slug=capitulo_slug)
    
    def form_valid(self, form):
        """Exibe mensagem de sucesso ao atualizar a página."""
        messages.success(self.request, 'Página atualizada com sucesso!')
        return super().form_valid(form)
    
    def get_success_url(self):
        """Redireciona para a página do capítulo após a atualização da página."""
        return self.object.capitulo.get_absolute_url()

class PaginaDeleteView(LoginRequiredMixin, PageOwnerOrStaffMixin, DeleteView):
    """
    View para excluir uma página existente.
    Apenas o criador do mangá relacionado, membros da equipe ou superusuários podem acessar.
    """
    model = Pagina
    template_name = 'mangas/pagina_confirm_delete.html'
    
    def get_queryset(self):
        """Filtra as páginas pelo capítulo relacionado."""
        capitulo_slug = self.kwargs.get('capitulo_slug')
        return Pagina.objects.filter(capitulo__slug=capitulo_slug)
    
    def delete(self, request, *args, **kwargs):
        """Exibe mensagem de sucesso ao excluir a página."""
        messages.success(request, 'Página excluída com sucesso!')
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        """Redireciona para a página do capítulo após a exclusão da página."""
        return self.object.capitulo.get_absolute_url()

# NOVA: View para criação de capítulo completo
class CapituloCompleteCreateView(LoginRequiredMixin, ChapterOwnerOrStaffMixin, CreateView):
    """
    View para criação de capítulo completo com upload de arquivo compactado.
    
    Permite o upload de um arquivo .zip, .rar, .cbz ou .cbr contendo as páginas
    do capítulo, que serão extraídas e salvas automaticamente.
    """
    model = Capitulo
    form_class = CapituloCompleteForm
    template_name = 'mangas/capitulo_complete_form.html'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_processor = MangaFileProcessorService()
    
    def get_initial(self):
        """Define os valores iniciais do formulário."""
        initial = super().get_initial()
        self.manga = Manga.objects.get(slug=self.kwargs['manga_slug'])
        initial['manga'] = self.manga
        return initial
    
    def form_valid(self, form):
        """
        Processa o formulário quando os dados são válidos.
        
        Se arquivos forem fornecidos (como pasta ou arquivo compactado), 
        processa-os para extrair as páginas do capítulo.
        """
        # Define o mangá e o criador do capítulo
        form.instance.manga = self.manga
        form.instance.criado_por = self.request.user
        
        # Salva o capítulo para obter um ID
        self.object = form.save()
        
        # Processa os arquivos enviados, se houver
        arquivos = self.request.FILES.getlist('arquivos')
        if arquivos:
            try:
                # Delega o processamento para o serviço
                self.file_processor.process_chapter_files(
                    chapter=self.object,
                    files=arquivos,
                    user=self.request.user
                )
                messages.success(self.request, 'Capítulo e páginas processados com sucesso!')
            except Exception as e:
                # Em caso de erro, remove o capítulo criado
                self.object.delete()
                logger.error(f'Erro ao processar arquivos do capítulo: {str(e)}')
                messages.error(
                    self.request,
                    f'Erro ao processar os arquivos: {str(e)}. Por favor, tente novamente.'
                )
                return self.form_invalid(form)
        
        return super().form_valid(form)
    
    def get_success_url(self):
        """Redireciona para a página do mangá após a criação do capítulo."""
        return self.object.manga.get_absolute_url()
    
    def test_func(self):
        """Verifica se o usuário tem permissão para criar capítulos."""
        return self.request.user.is_staff or self.request.user.is_superuser
