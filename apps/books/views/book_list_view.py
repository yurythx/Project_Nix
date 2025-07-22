from django.views import View
from django.shortcuts import render
from apps.books.services.book_service import BookService

class BookListView(View):
    template_name = 'books/book_list.html'
    service_class = BookService

    def get(self, request):
        service = self.service_class()
        books = service.list_books()
        return render(request, self.template_name, {'books': books}) 