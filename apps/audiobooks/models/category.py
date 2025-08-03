from django.db import models
from django.utils.text import slugify
from django.urls import reverse

class Category(models.Model):
    """
    Modelo para categorias de vídeos
    
    Princípios SOLID aplicados:
    - Single Responsibility: Apenas responsável por representar categorias
    - Open/Closed: Extensível via herança
    """
    name = models.CharField('Nome', max_length=100)
    description = models.TextField('Descrição', blank=True)
    slug = models.SlugField('Slug', unique=True, blank=True)
    icon = models.CharField('Ícone', max_length=50, blank=True, 
                          help_text='Nome do ícone FontAwesome (ex: fa-podcast)')
    is_active = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        app_label = 'audiobooks'
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            self.slug = base_slug
            counter = 1
            while Category.objects.filter(slug=self.slug).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('audiobooks:category_detail', kwargs={'slug': self.slug})
    
    def get_videos_count(self):
        """Retorna o número de vídeos nesta categoria"""
        return self.videos.filter(is_public=True).count()