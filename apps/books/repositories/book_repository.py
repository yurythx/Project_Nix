from apps.books.interfaces.book_repository_interface import BookRepositoryInterface
from apps.books.models.book import Book
from django.shortcuts import get_object_or_404

class BookRepository(BookRepositoryInterface):
    def list_all(self):
        return Book.objects.all()

    def get_by_slug(self, slug):
        return get_object_or_404(Book, slug=slug)

    def create(self, data):
        return Book.objects.create(**data)

    def update(self, slug, data):
        book = self.get_by_slug(slug)
        for key, value in data.items():
            setattr(book, key, value)
        book.save()
        return book

    def delete(self, slug):
        book = self.get_by_slug(slug)
        book.delete() 