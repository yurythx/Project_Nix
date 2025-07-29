from django.http import JsonResponse
from django.core.paginator import Paginator
from .manga_views import Capitulo
from ..models.pagina import Pagina

def capitulo_paginas_lazy(request, manga_slug, capitulo_slug):
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 10))
    
    # Filtra capítulos publicados para usuários não autenticados ou sem permissões
    if not request.user.is_authenticated or not request.user.is_staff:
        capitulo = Capitulo.objects.filter(is_published=True).get(slug=capitulo_slug, volume__manga__slug=manga_slug)
    else:
        capitulo = Capitulo.objects.get(slug=capitulo_slug, volume__manga__slug=manga_slug)
    
    paginas = Pagina.objects.filter(capitulo=capitulo).order_by('number')
    paginator = Paginator(paginas, per_page)
    page_obj = paginator.get_page(page)
    data = [
        {
            'number': p.number,
            'url': p.image.url if p.image and hasattr(p.image, 'url') else '',
            'caption': f'Página {p.number}'
        } for p in page_obj.object_list
    ]
    return JsonResponse({
        'pages': data,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'num_pages': paginator.num_pages,
        'current_page': page_obj.number,
        'total': paginator.count
    }) 