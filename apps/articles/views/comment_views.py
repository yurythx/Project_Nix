"""
Views para sistema de comentários dos artigos.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.contrib import messages
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_protect
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited
import json
from django.template.loader import render_to_string

from apps.articles.models.article import Article
from apps.articles.models.comment import Comment
from apps.articles.forms import CommentForm, ReplyForm, CommentModerationForm
from apps.articles.services.comment_service import CommentService
from apps.articles.repositories.comment_repository import CommentRepository
from apps.articles.services.article_service import ArticleService
from apps.articles.repositories.article_repository import DjangoArticleRepository


def get_client_ip(request):
    """Obter IP do cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@csrf_protect
@ratelimit(key='ip', rate='10/h', method='POST', block=True)
def add_comment(request, slug):
    """Adicionar comentário a um artigo"""
    print('DEBUG SESSION:', request.session.session_key)
    print('DEBUG USER:', request.user, getattr(request.user, 'is_authenticated', None))
    print('DEBUG POST:', request.POST)
    try:
        article = get_object_or_404(Article, slug=slug, status='published')
        comment_service = CommentService(CommentRepository())
        if not article.allow_comments:
            messages.error(request, 'Comentários não são permitidos neste artigo.')
            return redirect('articles:article_detail', slug=slug)
        if request.method == 'POST':
            form = CommentForm(request.POST, user=request.user if request.user.is_authenticated else None, article=article)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                if form.is_valid():
                    comment = form.save()
                    if comment.is_approved:
                        if comment.parent:
                            reply_html = render_to_string('articles/comments/reply_snippet.html', {'reply': comment})
                            return JsonResponse({'success': True, 'is_approved': True, 'reply_html': reply_html})
                        else:
                            comment_html = render_to_string('articles/comments/comment_snippet.html', {'comment': comment})
                            return JsonResponse({'success': True, 'is_approved': True, 'comment_html': comment_html})
                    else:
                        return JsonResponse({'success': True, 'is_approved': False, 'message': 'Comentário enviado para moderação.'})
                else:
                    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                        errors = {}
                        if form.errors and hasattr(form.errors, 'get_json_data'):
                            errors = form.errors.get_json_data()
                        return JsonResponse({'success': False, 'errors': errors})
                    messages.error(request, f'❌ Ocorreu um erro ao enviar o comentário. Verifique os campos e tente novamente.\n{form.errors}')
                    return redirect('articles:article_detail', slug=slug)
            else:
                messages.success(request, '💬 Seu comentário foi publicado com sucesso. Obrigado por contribuir!')
                return redirect('articles:article_detail', slug=slug)
        return redirect('articles:article_detail', slug=slug)
    except Ratelimited:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Você enviou comentários demais. Tente novamente mais tarde.'}, status=429)
        messages.error(request, 'Você enviou comentários demais. Tente novamente mais tarde.')
        return redirect('articles:article_detail', slug=slug)


@csrf_protect
@ratelimit(key='ip', rate='10/h', method='POST', block=True)
def add_reply(request, slug, comment_id):
    """Adicionar resposta a um comentário"""
    try:
        article = get_object_or_404(Article, slug=slug, status='published')
        parent_comment = get_object_or_404(Comment, id=comment_id, article=article)
        comment_service = CommentService(CommentRepository())
        if not article.allow_comments:
            messages.error(request, 'Comentários não são permitidos neste artigo.')
            return redirect('articles:article_detail', slug=slug)
        if not parent_comment.can_be_replied:
            messages.error(request, 'Este comentário não pode receber respostas.')
            return redirect('articles:article_detail', slug=slug)
        if request.method == 'POST':
            form = ReplyForm(request.POST, user=request.user if request.user.is_authenticated else None, article=article, parent=parent_comment)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                if form.is_valid():
                    reply = form.save()
                    if reply.is_approved:
                        reply_html = render_to_string('articles/comments/reply_snippet.html', {'reply': reply})
                        return JsonResponse({'success': True, 'is_approved': True, 'reply_html': reply_html})
                    else:
                        return JsonResponse({'success': True, 'is_approved': False, 'message': 'Resposta enviada para moderação.'})
                else:
                    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                        errors = {}
                        if form.errors and hasattr(form.errors, 'get_json_data'):
                            errors = form.errors.get_json_data()
                        return JsonResponse({'success': False, 'errors': errors})
                    # Renderizar a página de detalhe do artigo com o reply_form e o id do comentário pai
                    article_service = ArticleService(DjangoArticleRepository())
                    article_obj = article_service.get_article_by_slug(slug)
                    related_articles = article_service.get_related_articles(article_obj, limit=3)
                    comments = article_obj.comments.filter(is_approved=True, parent__isnull=True).order_by('-created_at')[:5]
                    context = {
                        'article': article_obj,
                        'related_articles': related_articles,
                        'comments': comments,
                        'comment_count': article_obj.comments.filter(is_approved=True).count(),
                        'reply_form': form,
                        'reply_parent_id': parent_comment.id,
                    }
                    return render(request, 'articles/article_detail.html', context)
            else:
                messages.success(request, 'Resposta publicada com sucesso!')
                return redirect('articles:article_detail', slug=slug)
        return redirect('articles:article_detail', slug=slug)
    except Ratelimited:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Você enviou respostas demais. Tente novamente mais tarde.'}, status=429)
        messages.error(request, 'Você enviou respostas demais. Tente novamente mais tarde.')
        return redirect('articles:article_detail', slug=slug)


def comment_list(request, slug):
    """Listar comentários de um artigo (AJAX)"""
    article = get_object_or_404(Article, slug=slug, status='published')
    comments = Comment.objects.filter(
        article=article,
        is_approved=True,
        parent__isnull=True
    ).select_related('user').prefetch_related('replies').order_by('-created_at')
    paginator = Paginator(comments, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    context = {
        'article': article,
        'comments': page_obj,
        'comment_form': CommentForm(user=request.user if request.user.is_authenticated else None, article=article),
    }
    return render(request, 'articles/comments/comment_list.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def moderate_comments(request):
    """Painel de moderação de comentários (apenas staff)"""
    # Filtros
    status_filter = request.GET.get('status', 'pending')
    search = request.GET.get('search', '')
    
    # Query base
    comments = Comment.objects.select_related('article', 'user', 'parent')
    
    # Aplicar filtros
    if status_filter == 'pending':
        comments = comments.filter(is_approved=False, is_spam=False)
    elif status_filter == 'approved':
        comments = comments.filter(is_approved=True)
    elif status_filter == 'spam':
        comments = comments.filter(is_spam=True)
    
    # Busca
    if search:
        comments = comments.filter(
            Q(content__icontains=search) |
            Q(name__icontains=search) |
            Q(email__icontains=search) |
            Q(article__title__icontains=search)
        )
    
    # Ordenação
    comments = comments.order_by('-created_at')
    
    # Paginação
    paginator = Paginator(comments, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Estatísticas
    stats = {
        'total': Comment.objects.count(),
        'pending': Comment.objects.filter(is_approved=False, is_spam=False).count(),
        'approved': Comment.objects.filter(is_approved=True).count(),
        'spam': Comment.objects.filter(is_spam=True).count(),
    }
    
    context = {
        'comments': page_obj,
        'stats': stats,
        'status_filter': status_filter,
        'search': search,
    }
    
    return render(request, 'articles/comments/moderation.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
@require_POST
def moderate_comment_action(request, comment_id):
    """Ações de moderação em comentários"""
    comment = get_object_or_404(Comment, id=comment_id)
    action = request.POST.get('action')
    
    if action == 'approve':
        comment.approve()
        messages.success(request, f'Comentário de {comment.author_name} aprovado.')
    
    elif action == 'spam':
        comment.mark_as_spam()
        messages.warning(request, f'Comentário de {comment.author_name} marcado como spam.')
    
    elif action == 'delete':
        author_name = comment.author_name
        comment.delete()
        messages.info(request, f'Comentário de {author_name} excluído.')
    
    # Para AJAX
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'action': action})
    
    return redirect('articles:moderate_comments')


@require_http_methods(["GET"])
def comment_stats(request):
    """Estatísticas de comentários (API)"""
    if not request.user.is_staff:
        return HttpResponseForbidden()
    
    # Estatísticas gerais
    total_comments = Comment.objects.count()
    approved_comments = Comment.objects.filter(is_approved=True).count()
    pending_comments = Comment.objects.filter(is_approved=False, is_spam=False).count()
    spam_comments = Comment.objects.filter(is_spam=True).count()
    
    # Comentários por artigo (top 10)
    top_articles = Article.objects.annotate(
        comment_count=Count('comments', filter=Q(comments__is_approved=True))
    ).order_by('-comment_count')[:10]
    
    # Comentários recentes
    recent_comments = Comment.objects.filter(
        is_approved=True
    ).select_related('article').order_by('-created_at')[:5]
    
    data = {
        'total_comments': total_comments,
        'approved_comments': approved_comments,
        'pending_comments': pending_comments,
        'spam_comments': spam_comments,
        'approval_rate': round((approved_comments / total_comments * 100) if total_comments > 0 else 0, 1),
        'top_articles': [
            {
                'title': article.title,
                'slug': article.slug,
                'comment_count': article.comment_count
            }
            for article in top_articles
        ],
        'recent_comments': [
            {
                'id': comment.id,
                'author_name': comment.author_name,
                'content': comment.content[:100] + '...' if len(comment.content) > 100 else comment.content,
                'article_title': comment.article.title,
                'created_at': comment.created_at.isoformat()
            }
            for comment in recent_comments
        ]
    }
    
    return JsonResponse(data)


def load_more_comments(request):
    article_id = request.GET.get('article_id')
    page = request.GET.get('page', 1)
    article = get_object_or_404(Article, id=article_id)
    comments = Comment.objects.filter(article=article, parent=None, is_approved=True).order_by('created_at')
    paginator = Paginator(comments, 10)
    page_obj = paginator.get_page(page)
    html = render_to_string('articles/comments/comment_list_partial.html', {'comments': page_obj})
    return HttpResponse(html)


def load_replies(request, comment_id):
    parent = get_object_or_404(Comment, id=comment_id)
    replies = parent.replies.filter(is_approved=True).order_by('created_at')
    html = render_to_string('articles/comments/reply_list_partial.html', {'replies': replies})
    return HttpResponse(html)
