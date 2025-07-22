from django.db import models
from django.utils.text import slugify

class Manga(models.Model):
    title = models.CharField('Título', max_length=200)
    author = models.CharField('Autor', max_length=120, blank=True)
    description = models.TextField('Descrição', blank=True)
    cover_image = models.ImageField('Capa', upload_to='mangas/covers/', null=True, blank=True)
    slug = models.SlugField('Slug', unique=True, blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Mangá'
        verbose_name_plural = 'Mangás'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('mangas:manga_detail', kwargs={'slug': self.slug})

class Capitulo(models.Model):
    manga = models.ForeignKey(Manga, on_delete=models.CASCADE, related_name='capitulos')
    number = models.PositiveIntegerField('Número do Capítulo')
    title = models.CharField('Título', max_length=200, blank=True)
    slug = models.SlugField('Slug', unique=True, blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Capítulo'
        verbose_name_plural = 'Capítulos'
        ordering = ['number']
        unique_together = ('manga', 'number')

    def save(self, *args, **kwargs):
        if not self.slug:
            base = self.title or f'capitulo-{self.number}'
            self.slug = slugify(f'{self.manga.title}-{base}')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.manga.title} - Capítulo {self.number}'

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('mangas:capitulo_detail', kwargs={'manga_slug': self.manga.slug, 'capitulo_slug': self.slug})

class Pagina(models.Model):
    capitulo = models.ForeignKey(Capitulo, on_delete=models.CASCADE, related_name='paginas')
    number = models.PositiveIntegerField('Número da Página')
    image = models.ImageField('Imagem', upload_to='mangas/pages/')
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Página'
        verbose_name_plural = 'Páginas'
        ordering = ['number']
        unique_together = ('capitulo', 'number')

    def __str__(self):
        return f'{self.capitulo} - Página {self.number}' 