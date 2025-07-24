"""
Views para sistema de comentários dos artigos.
"""

from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django_ratelimit.decorators import ratelimit
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.template.loader import render_to_string
from django.urls import reverse_lazy
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


class CommentCreateView(View):
    """CBV para adicionar comentário a um artigo"""
    @method_decorator(csrf_protect)
    @method_decorator(ratelimit(key='ip', rate='10/h', method='POST', block=True))
    def post(self, request, slug):
        article = get_object_or_404(Article, slug=slug, status='published')
        comment_service = CommentService(CommentRepository())
        if not article.allow_comments:
            messages.error(request, 'Comentários não são permitidos neste artigo.')
            return redirect('articles:article_detail', slug=slug)
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
                errors = form.errors.get_json_data() if hasattr(form.errors, 'get_json_data') else {}
                return JsonResponse({'success': False, 'errors': errors})
        else:
            if form.is_valid():
                form.save()
                messages.success(request, '💬 Seu comentário foi publicado com sucesso. Obrigado por contribuir!')
            else:
                messages.error(request, f'❌ Ocorreu um erro ao enviar o comentário. Verifique os campos e tente novamente.\n{form.errors}')
            return redirect('articles:article_detail', slug=slug)


class ReplyCreateView(View):
    """CBV para adicionar resposta a um comentário"""
    @method_decorator(csrf_protect)
    @method_decorator(ratelimit(key='ip', rate='10/h', method='POST', block=True))
    def post(self, request, slug, comment_id):
        article = get_object_or_404(Article, slug=slug, status='published')
        parent_comment = get_object_or_404(Comment, id=comment_id, article=article)
        comment_service = CommentService(CommentRepository())
        if not article.allow_comments:
            messages.error(request, 'Comentários não são permitidos neste artigo.')
            return redirect('articles:article_detail', slug=slug)
        if not parent_comment.can_be_replied:
            messages.error(request, 'Este comentário não pode receber respostas.')
            return redirect('articles:article_detail', slug=slug)
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
                errors = form.errors.get_json_data() if hasattr(form.errors, 'get_json_data') else {}
                return JsonResponse({'success': False, 'errors': errors})
        else:
            if form.is_valid():
                form.save()
                messages.success(request, 'Resposta publicada com sucesso!')
            else:
                messages.error(request, 'Erro ao publicar resposta.')
            return redirect('articles:article_detail', slug=slug)


class CommentListView(View):
    """CBV para listar comentários de um artigo (AJAX)"""
    def get(self, request, slug):
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


class CommentModerationView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """CBV para painel de moderação de comentários (apenas staff)"""
    model = Comment
    template_name = 'articles/comments/moderation.html'
    context_object_name = 'comments'
    paginate_by = 20

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        status_filter = self.request.GET.get('status', 'pending')
        search = self.request.GET.get('search', '')
        comments = Comment.objects.select_related('article', 'user', 'parent')
        if status_filter == 'pending':
            comments = comments.filter(is_approved=False, is_spam=False)
        elif status_filter == 'approved':
            comments = comments.filter(is_approved=True)
        elif status_filter == 'spam':
            comments = comments.filter(is_spam=True)
        if search:
            comments = comments.filter(
                Q(content__icontains=search) |
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(article__title__icontains=search)
            )
        return comments.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = {
            'total': Comment.objects.count(),
            'pending': Comment.objects.filter(is_approved=False, is_spam=False).count(),
            'approved': Comment.objects.filter(is_approved=True).count(),
            'spam': Comment.objects.filter(is_spam=True).count(),
        }
        context['status_filter'] = self.request.GET.get('status', 'pending')
        context['search'] = self.request.GET.get('search', '')
        return context


class CommentModerationActionView(LoginRequiredMixin, UserPassesTestMixin, View):
    """CBV para ações de moderação em comentários"""
    def test_func(self):
        return self.request.user.is_staff

    def post(self, request, comment_id):
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
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'action': action})
        return redirect('articles:moderate_comments')


class CommentStatsView(LoginRequiredMixin, UserPassesTestMixin, View):
    """CBV para estatísticas de comentários (API)"""
    def test_func(self):
        return self.request.user.is_staff

    def get(self, request):
        total_comments = Comment.objects.count()
        approved_comments = Comment.objects.filter(is_approved=True).count()
        pending_comments = Comment.objects.filter(is_approved=False, is_spam=False).count()
        spam_comments = Comment.objects.filter(is_spam=True).count()
        top_articles = Article.objects.annotate(
            comment_count=Count('comments', filter=Q(comments__is_approved=True))
        ).order_by('-comment_count')[:10]
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


class LoadMoreCommentsView(View):
    def get(self, request):
        article_id = request.GET.get('article_id')
        page = request.GET.get('page', 1)
        article = get_object_or_404(Article, id=article_id)
        comments = Comment.objects.filter(article=article, parent=None, is_approved=True).order_by('created_at')
        paginator = Paginator(comments, 10)
        page_obj = paginator.get_page(page)
        html = render_to_string('articles/comments/comment_list_partial.html', {'comments': page_obj})
        return HttpResponse(html)


class LoadRepliesView(View):
    def get(self, request, comment_id):
        parent = get_object_or_404(Comment, id=comment_id)
        replies = parent.replies.filter(is_approved=True).order_by('created_at')
        html = render_to_string('articles/comments/reply_list_partial.html', {'replies': replies})
        return HttpResponse(html)
