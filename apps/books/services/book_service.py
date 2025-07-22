from apps.books.repositories.book_repository import BookRepository

class BookService:
    def __init__(self, repository=None):
        self.repository = repository or BookRepository()

    def list_books(self):
        return self.repository.list_all()

    def get_book(self, slug):
        return self.repository.get_by_slug(slug)

    def create_book(self, data):
        # Aqui pode adicionar validações de negócio
        return self.repository.create(data)

    def update_book(self, slug, data):
        return self.repository.update(slug, data)

    def delete_book(self, slug):
        return self.repository.delete(slug) 