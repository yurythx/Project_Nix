import logging
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import Http404
from django.db import models

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
    
    def get_queryset(self):
        """Otimiza a consulta ao banco de dados usando select_related e prefetch_related."""
        return Manga.objects.prefetch_related(
            models.Prefetch(
                'volumes',
                queryset=Volume.objects.order_by('number').prefetch_related(
                    models.Prefetch(
                        'capitulos',
                        queryset=Capitulo.objects.order_by('number').annotate(
                            num_paginas=models.Count('paginas')
                        ).select_related('volume')
                    )
                )
            )
        )
    
    def get_context_data(self, **kwargs):
        """Adiciona a lista de volumes e capítulos ao contexto."""
        context = super().get_context_data(**kwargs)
        
        # Obtém o mangá do contexto
        manga = context['manga']
        
        # Conta o número total de capítulos e páginas
        total_capitulos = Capitulo.objects.filter(volume__manga=manga).count()
        total_paginas = Pagina.objects.filter(capitulo__volume__manga=manga).count()
        
        # Obtém os volumes já pré-carregados na consulta principal
        volumes = list(manga.volumes.all())
        
        # Configura a paginação para volumes
        paginator = Paginator(volumes, self.paginate_by)
        page = self.request.GET.get('page')
        
        try:
            volumes_paginados = paginator.page(page)
        except PageNotAnInteger:
            # Se a página não for um inteiro, exibe a primeira página
            volumes_paginados = paginator.page(1)
        except EmptyPage:
            # Se a página estiver fora do alcance, exibe a última página
            volumes_paginados = paginator.page(paginator.num_pages)
        
        # Adiciona informações adicionais ao contexto
        context.update({
            'volumes': volumes_paginados,
            'total_capitulos': total_capitulos,
            'total_paginas': total_paginas,
            'has_volumes': len(volumes) > 0,
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
    
    def get_success_url(self):
        """Redireciona para a lista de mangás após a criação."""
        messages.success(self.request, 'Mangá criado com sucesso!')
        return reverse_lazy('mangas:manga_list')
    
    def form_valid(self, form):
        """Define o usuário atual como criador do mangá."""
        form.instance.criado_por = self.request.user
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
    
    def get_success_url(self):
        """Redireciona para a lista de mangás após a atualização."""
        messages.success(self.request, 'Mangá atualizado com sucesso!')
        return reverse_lazy('mangas:manga_list')
    
    def form_valid(self, form):
        """Define o usuário atual como o último a modificar o mangá."""
        form.instance.atualizado_por = self.request.user
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
        """Otimiza a consulta ao banco de dados para incluir o volume e o mangá relacionados."""
        manga_slug = self.kwargs.get('manga_slug')
        return (
            Capitulo.objects
            .filter(manga__slug=manga_slug)
            .select_related('volume', 'manga')
            .prefetch_related('paginas')
            .annotate(
                num_paginas=models.Count('paginas'),
                capitulo_anterior_id=models.Subquery(
                    Capitulo.objects.filter(
                        manga__slug=manga_slug,
                        number__lt=models.OuterRef('number'),
                        volume=models.OuterRef('volume')
                    )
                    .order_by('-number')
                    .values('id')[:1]
                ),
                proximo_capitulo_id=models.Subquery(
                    Capitulo.objects.filter(
                        manga__slug=manga_slug,
                        number__gt=models.OuterRef('number'),
                        volume=models.OuterRef('volume')
                    )
                    .order_by('number')
                    .values('id')[:1]
                )
            )
        )
    
    def get_context_data(self, **kwargs):
        """Adiciona informações adicionais ao contexto, como páginas e navegação entre capítulos."""
        context = super().get_context_data(**kwargs)
        capitulo = self.get_object()
        
        # Obtém todas as páginas ordenadas por número
        paginas = list(capitulo.paginas.all().order_by('number'))
        
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
            
        # Obtém o índice da página atual para navegação
        current_page_index = paginas_paginadas.number - 1
        
        # Calcula o progresso de leitura
        total_paginas = len(paginas)
        progresso = int((current_page_index + 1) / total_paginas * 100) if total_paginas > 0 else 0
        
        # Adiciona informações ao contexto
        context.update({
            'paginas': paginas_paginadas,
            'total_paginas': total_paginas,
            'pagina_atual': current_page_index + 1,
            'progresso': progresso,
            'capitulo_anterior': Capitulo.objects.filter(id=capitulo.capitulo_anterior_id).first() if hasattr(capitulo, 'capitulo_anterior_id') else None,
            'proximo_capitulo': Capitulo.objects.filter(id=capitulo.proximo_capitulo_id).first() if hasattr(capitulo, 'proximo_capitulo_id') else None,
            'outros_capitulos_volume': list(
                Capitulo.objects
                .filter(volume=capitulo.volume)
                .exclude(id=capitulo.id)
                .order_by('number')
                .values('id', 'number', 'title')
            ) if capitulo.volume else [],
            'volumes': list(
                Volume.objects
                .filter(manga=capitulo.manga)
                .annotate(
                    capitulo_count=models.Count('capitulos'),
                    pagina_count=models.Count('capitulos__paginas')
                )
                .order_by('number')
                .values('id', 'number', 'title', 'capitulo_count', 'pagina_count')
            )
        })
        
        return context

class CapituloCreateView(LoginRequiredMixin, StaffOrSuperuserRequiredMixin, CreateView):
    """
    View para criar um novo capítulo.
    Apenas membros da equipe ou superusuários podem acessar.
    """
    model = Capitulo
    form_class = CapituloForm
    template_name = 'mangas/pagina_form.html'
    
    def get_initial(self):
        """Define o mangá e o volume relacionados ao capítulo."""
        self.manga = Manga.objects.get(slug=self.kwargs['manga_slug'])
        initial = {'manga': self.manga}
        
        # Verifica se foi passado um volume_id na URL (ex: ?volume=1)
        volume_id = self.request.GET.get('volume')
        if volume_id:
            try:
                volume = Volume.objects.get(id=volume_id, manga=self.manga)
                initial['volume'] = volume
            except Volume.DoesNotExist:
                pass
                
        return initial
    
    def form_valid(self, form):
        """Define o mangá, volume e o criador do capítulo."""
        form.instance.manga = self.manga
        form.instance.criado_por = self.request.user
        
        # Se não foi especificado um volume, atribui ao volume padrão (volume 0)
        if not form.instance.volume:
            form.instance.volume, _ = Volume.objects.get_or_create(
                manga=self.manga,
                number=0,
                defaults={
                    'title': 'Sem Volume',
                    'criado_por': self.request.user
                }
            )
            
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
    template_name = 'mangas/pagina_form.html'
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
    template_name = 'mangas/manga_confirm_delete.html'
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
    template_name = 'mangas/manga_confirm_delete.html'
    
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
        """Define os valores iniciais do formulário, incluindo o volume se especificado."""
        try:
            self.manga = Manga.objects.get(slug=self.kwargs['manga_slug'])
            initial = {'manga': self.manga}
            
            # Verifica se foi passado um volume_id na URL (ex: ?volume=1)
            volume_id = self.request.GET.get('volume')
            if volume_id:
                try:
                    volume = Volume.objects.get(id=volume_id, manga=self.manga)
                    initial['volume'] = volume
                except Volume.DoesNotExist:
                    pass
                    
            return initial
        except Manga.DoesNotExist:
            raise Http404("Mangá não encontrado")
    
    def form_valid(self, form):
        """
        Processa o formulário quando os dados são válidos.
        
        Se arquivos forem fornecidos (como pasta ou arquivo compactado), 
        processa-os para extrair as páginas do capítulo.
        """
        try:
            # Define o mangá e o criador do capítulo
            form.instance.manga = form.cleaned_data['manga']
            form.instance.criado_por = self.request.user
            
            # Se não foi especificado um volume, atribui ao volume padrão (volume 0)
            if not form.instance.volume:
                form.instance.volume, _ = Volume.objects.get_or_create(
                    manga=form.instance.manga,
                    number=0,
                    defaults={
                        'title': 'Sem Volume',
                        'criado_por': self.request.user
                    }
                )
            
            # Salva a instância do capítulo
            response = super().form_valid(form)
            
            # Processar arquivo(s) se fornecido(s)
            arquivos = form.cleaned_data.get('arquivo_capitulo')
            if arquivos:
                # Se for uma lista (pasta), processa como múltiplos arquivos
                if isinstance(arquivos, list):
                    import io
                    import zipfile
                    from django.core.files.base import ContentFile
                    
                    # Cria um arquivo ZIP em memória
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                        for arquivo in arquivos:
                            # Adiciona cada arquivo ao ZIP com um nome que mantém a ordem
                            zip_file.writestr(arquivo.name, arquivo.read())
                    
                    # Prepara o arquivo ZIP para processamento
                    zip_buffer.seek(0)
                    arquivo_zip = ContentFile(zip_buffer.read(), name='capitulo_temp.zip')
                    
                    # Processa o arquivo ZIP
                    success, message = self.file_processor.process_chapter_file(self.object, arquivo_zip)
                else:
                    # Processa como um único arquivo compactado
                    success, message = self.file_processor.process_chapter_file(self.object, arquivos)
                
                if success:
                    messages.success(self.request, message)
                else:
                    messages.error(self.request, message)
                    # Se houver erro ao processar o arquivo, mantém o capítulo mas informa o problema
                    return self.render_to_response(self.get_context_data(form=form))
            
            return response
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Erro ao criar capítulo: {str(e)}", exc_info=True)
            messages.error(
                self.request, 
                f"Ocorreu um erro ao processar o arquivo do capítulo: {str(e)}"
            )
            return self.form_invalid(form)
    
    def get_success_url(self):
        """Redireciona para a página do mangá após a criação do capítulo."""
        return self.object.manga.get_absolute_url()
    
    def test_func(self):
        """Verifica se o usuário tem permissão para criar capítulos."""
        return self.request.user.is_staff or self.request.user.is_superuser