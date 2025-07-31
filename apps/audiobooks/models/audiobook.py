from django.conf import settings
from django.db import models
from django.utils.text import slugify
from django.urls import reverse

class VideoAudio(models.Model):
    # Informações básicas
    title = models.CharField('Título', max_length=200)
    description = models.TextField('Descrição', blank=True)
    slug = models.SlugField('Slug', unique=True, blank=True)
    
    # Metadados
    author = models.CharField('Autor/Criador', max_length=120, blank=True)
    narrator = models.CharField('Narrador/Apresentador', max_length=120, blank=True)
    published_date = models.DateField('Data de Publicação', null=True, blank=True)
    duration = models.DurationField('Duração', null=True, blank=True)
    
    # Mídia
    video_file = models.FileField('Arquivo de Vídeo', upload_to='videobooks/videos/', 
                                 null=True, blank=True, 
                                 help_text='Formatos suportados: MP4, WebM, OGG')
    thumbnail = models.ImageField('Thumbnail', upload_to='videobooks/thumbnails/', 
                                null=True, blank=True,
                                help_text='Imagem de capa do vídeo')
    external_url = models.URLField('URL Externa', blank=True, 
                                 help_text='Link para vídeo externo (YouTube, Vimeo, etc.)')
    
    # Categorização
    CATEGORY_CHOICES = [
        ('podcast', 'Podcast'),
        ('audiobook', 'Áudio Livro'),
        ('lecture', 'Aula/Palestra'),
        ('documentary', 'Documentário'),
        ('other', 'Outro'),
    ]
    category = models.CharField('Categoria', max_length=20, 
                              choices=CATEGORY_CHOICES, 
                              default='other')
    
    # Controle
    is_featured = models.BooleanField('Destaque', default=False)
    is_public = models.BooleanField('Público', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        app_label = 'audiobooks'
        verbose_name = 'Conteúdo em Vídeo'
        verbose_name_plural = 'Conteúdos em Vídeo'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['category']),
            models.Index(fields=['created_at']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            self.slug = base_slug
            counter = 1
            while VideoAudio.objects.filter(slug=self.slug).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('audiobooks:videobook_detail', kwargs={'slug': self.slug})
    
    def get_duration_display(self):
        if not self.duration:
            return "Duração não disponível"
        total_seconds = int(self.duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        if hours > 0:
            return f"{hours}h {minutes:02d}min"
        return f"{minutes}min {seconds:02d}s"

    def get_source_type(self):
        if self.video_file:
            return 'upload'
        if self.external_url:
            if 'youtube.com' in self.external_url or 'youtu.be' in self.external_url:
                return 'youtube'
            elif 'vimeo.com' in self.external_url:
                return 'vimeo'
        return 'unknown'


class VideoProgress(models.Model):
    """Acompanha o progresso do usuário em um vídeo"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    video = models.ForeignKey(VideoAudio, on_delete=models.CASCADE)
    current_time = models.FloatField('Tempo Atual (segundos)', default=0.0)
    is_completed = models.BooleanField('Concluído', default=False)
    last_played = models.DateTimeField('Última reprodução', auto_now=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        app_label = 'audiobooks'
        unique_together = ('user', 'video')
        verbose_name = 'Progresso de Vídeo'
        verbose_name_plural = 'Progressos de Vídeos'
        indexes = [
            models.Index(fields=['user', 'video']),
            models.Index(fields=['last_played']),
        ]

    def __str__(self):
        status = "Concluído" if self.is_completed else f"{int(self.current_time)}s"
        return f"{self.user} - {self.video} ({status})"

    def get_progress_percentage(self):
        if not self.video.duration or self.video.duration.total_seconds() == 0:
            return 0
        progress = (self.current_time / self.video.duration.total_seconds()) * 100
        return min(100, max(0, progress))

class VideoFavorite(models.Model):
    """Permite que usuários marquem vídeos como favoritos"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    video = models.ForeignKey(VideoAudio, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField('Adicionado em', auto_now_add=True)

    class Meta:
        app_label = 'audiobooks'
        unique_together = ('user', 'video')
        verbose_name = 'Vídeo Favorito'
        verbose_name_plural = 'Vídeos Favoritos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user} ♥ {self.video}"
