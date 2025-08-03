from django.conf import settings
from django.db import models
from django.utils.text import slugify
from .category import Category

class Book(models.Model):
    """
    Modelo para livros
    
    Princípios SOLID aplicados:
    - Single Responsibility: Apenas responsável por representar livros
    - Open/Closed: Extensível via herança
    """
    title = models.CharField('Título', max_length=200)
    author = models.CharField('Autor', max_length=120, blank=True)
    description = models.TextField('Descrição', blank=True)
    published_date = models.DateField('Data de Publicação', null=True, blank=True)
    cover_image = models.ImageField('Capa', upload_to='books/covers/', null=True, blank=True)
    file = models.FileField('Arquivo', upload_to='books/ebooks/', null=True, blank=True)
    slug = models.SlugField('Slug', unique=True, blank=True)
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='books',
        verbose_name='Categoria'
    )
    is_featured = models.BooleanField('Destaque', default=False)
    is_public = models.BooleanField('Público', default=True)
    views = models.PositiveIntegerField('Visualizações', default=0)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        app_label = 'books'
        verbose_name = 'Livro'
        verbose_name_plural = 'Livros'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['category']),
            models.Index(fields=['created_at']),
            models.Index(fields=['views']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('books:book_detail', kwargs={'slug': self.slug})

class BookProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    location = models.CharField('Localização EPUB/PDF', max_length=255)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        app_label = 'books'
        unique_together = ('user', 'book')
        verbose_name = 'Progresso de Leitura'
        verbose_name_plural = 'Progressos de Leitura'

    def __str__(self):
        return f"{self.user} - {self.book} @ {self.location}"

class BookFavorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    created_at = models.DateTimeField('Adicionado em', auto_now_add=True)

    class Meta:
        app_label = 'books'
        unique_together = ('user', 'book')
        verbose_name = 'Livro Favorito'
        verbose_name_plural = 'Livros Favoritos'

    def __str__(self):
        return f"{self.user} ♥ {self.book}"