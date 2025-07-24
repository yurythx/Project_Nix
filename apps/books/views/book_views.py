from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views import View
from apps.books.models.book import Book, BookProgress, BookFavorite
from apps.books.forms.book_form import BookForm

class BookListView(ListView):
    model = Book
    template_name = 'books/book_list.html'
    context_object_name = 'books'
    paginate_by = 12

    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(title__icontains=q)
        return queryset

class BookDetailView(DetailView):
    model = Book
    template_name = 'books/book_detail.html'
    context_object_name = 'book'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

class BookCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Book
    form_class = BookForm
    template_name = 'books/book_form.html'
    success_url = reverse_lazy('books:book_list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

class BookUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Book
    form_class = BookForm
    template_name = 'books/book_form.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    success_url = reverse_lazy('books:book_list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

class BookDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Book
    template_name = 'books/book_confirm_delete.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    success_url = reverse_lazy('books:book_list')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser 

class SaveBookProgressView(LoginRequiredMixin, View):
    @method_decorator(csrf_exempt)
    def post(self, request, slug):
        from django.http import HttpResponseBadRequest, JsonResponse
        book = Book.objects.get(slug=slug)
        location = request.POST.get('location')
        if not location:
            return HttpResponseBadRequest('Localização não informada')
        progress, _ = BookProgress.objects.update_or_create(
            user=request.user, book=book,
            defaults={'location': location}
        )
        return JsonResponse({'status': 'ok'})

class GetBookProgressView(LoginRequiredMixin, View):
    def get(self, request, slug):
        from django.http import HttpResponseBadRequest, JsonResponse
        book = Book.objects.get(slug=slug)
        try:
            progress = BookProgress.objects.get(user=request.user, book=book)
            return JsonResponse({'location': progress.location})
        except BookProgress.DoesNotExist:
            return JsonResponse({'location': None})

class FavoriteBookView(LoginRequiredMixin, View):
    def post(self, request, slug):
        from django.http import HttpResponseBadRequest, JsonResponse
        book = Book.objects.get(slug=slug)
        BookFavorite.objects.get_or_create(user=request.user, book=book)
        return JsonResponse({'status': 'favorited'})

class UnfavoriteBookView(LoginRequiredMixin, View):
    def post(self, request, slug):
        from django.http import HttpResponseBadRequest, JsonResponse
        book = Book.objects.get(slug=slug)
        BookFavorite.objects.filter(user=request.user, book=book).delete()
        return JsonResponse({'status': 'unfavorited'})

class IsFavoriteBookView(LoginRequiredMixin, View):
    def get(self, request, slug):
        from django.http import HttpResponseBadRequest, JsonResponse
        book = Book.objects.get(slug=slug)
        is_fav = BookFavorite.objects.filter(user=request.user, book=book).exists()
        return JsonResponse({'favorite': is_fav}) 