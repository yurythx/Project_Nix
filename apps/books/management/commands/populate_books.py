from django.core.management.base import BaseCommand
from apps.books.models.book import Book
from apps.books.models.category import Category

class Command(BaseCommand):
    help = 'Popula o banco com livros de exemplo'
    
    def handle(self, *args, **options):
        # Criar categorias
        categories = [
            {"name": "Ficção", "description": "Livros de ficção"},
            {"name": "Não-ficção", "description": "Livros de não-ficção"},
            {"name": "Técnico", "description": "Livros técnicos"}
        ]
        
        for cat_data in categories:
            category, created = Category.objects.get_or_create(
                name=cat_data["name"],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f"Categoria criada: {category.name}")
        
        # Criar livros de exemplo
        books = [
            {
                "title": "Dom Casmurro",
                "author": "Machado de Assis",
                "description": "Um clássico da literatura brasileira",
                "category": Category.objects.get(name="Ficção")
            },
            {
                "title": "Clean Code",
                "author": "Robert C. Martin",
                "description": "Um manual de desenvolvimento ágil de software",
                "category": Category.objects.get(name="Técnico")
            }
        ]
        
        for book_data in books:
            book, created = Book.objects.get_or_create(
                title=book_data["title"],
                defaults={
                    **book_data,
                    "is_public": True
                }
            )
            if created:
                self.stdout.write(f"Livro criado: {book.title} | Slug: {book.slug}")
        
        self.stdout.write(self.style.SUCCESS('Dados populados com sucesso!'))