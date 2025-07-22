from django.conf import settings
from django.db import models
from django.utils.text import slugify

class Audiobook(models.Model):
    title = models.CharField('Título', max_length=200)
    author = models.CharField('Autor', max_length=120, blank=True)
    narrator = models.CharField('Narrador', max_length=120, blank=True)
    description = models.TextField('Descrição', blank=True)
    published_date = models.DateField('Data de Publicação', null=True, blank=True)
    duration = models.DurationField('Duração', null=True, blank=True)
    cover_image = models.ImageField('Capa', upload_to='audiobooks/covers/', null=True, blank=True)
    audio_file = models.FileField('Arquivo de Áudio', upload_to='audiobooks/files/', null=True, blank=True)
    slug = models.SlugField('Slug', unique=True, blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        app_label = 'audiobooks'
        verbose_name = 'Audiolivro'
        verbose_name_plural = 'Audiolivros'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('audiobooks:audiobook_detail', kwargs={'slug': self.slug})

class AudiobookProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    audiobook = models.ForeignKey(Audiobook, on_delete=models.CASCADE)
    current_time = models.DurationField('Tempo Atual', default='00:00:00')
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        app_label = 'audiobooks'
        unique_together = ('user', 'audiobook')
        verbose_name = 'Progresso de Audiolivro'
        verbose_name_plural = 'Progressos de Audiolivros'

    def __str__(self):
        return f"{self.user} - {self.audiobook} @ {self.current_time}"

class AudiobookFavorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    audiobook = models.ForeignKey(Audiobook, on_delete=models.CASCADE)
    created_at = models.DateTimeField('Adicionado em', auto_now_add=True)

    class Meta:
        app_label = 'audiobooks'
        unique_together = ('user', 'audiobook')
        verbose_name = 'Audiolivro Favorito'
        verbose_name_plural = 'Audiolivros Favoritos'

    def __str__(self):
        return f"{self.user} ♥ {self.audiobook}"
