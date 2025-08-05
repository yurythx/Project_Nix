from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .book import Book


class ReadingSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    pages_read = models.IntegerField(default=0)
    reading_speed = models.FloatField(null=True, blank=True)  # palavras por minuto
    current_page = models.IntegerField(default=1)
    device_type = models.CharField(max_length=20, choices=[
        ('desktop', 'Desktop'),
        ('mobile', 'Mobile'),
        ('tablet', 'Tablet'),
    ], default='desktop')
    location = models.CharField(max_length=100, blank=True)  # localização de leitura
    
    class Meta:
        ordering = ['-start_time']
    
    @property
    def duration(self):
        if self.end_time:
            return self.end_time - self.start_time
        return None
    
    @property
    def duration_minutes(self):
        duration = self.duration
        if duration:
            return duration.total_seconds() / 60
        return 0
    
    def __str__(self):
        return f"{self.user.username} - {self.book.title} ({self.start_time.strftime('%d/%m/%Y %H:%M')})"


class ReadingStatistics(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    total_reading_time = models.DurationField(default=timedelta())
    total_pages_read = models.IntegerField(default=0)
    total_books_completed = models.IntegerField(default=0)
    average_reading_speed = models.FloatField(default=0.0)  # palavras por minuto
    favorite_reading_time = models.TimeField(null=True, blank=True)
    longest_session = models.DurationField(default=timedelta())
    current_streak = models.IntegerField(default=0)  # dias consecutivos lendo
    best_streak = models.IntegerField(default=0)
    last_reading_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Reading Statistics"
        verbose_name_plural = "Reading Statistics"
    
    def update_statistics(self):
        """Atualiza as estatísticas baseadas nas sessões de leitura"""
        sessions = ReadingSession.objects.filter(user=self.user, end_time__isnull=False)
        
        # Total de tempo de leitura
        total_time = timedelta()
        total_pages = 0
        speeds = []
        
        for session in sessions:
            if session.duration:
                total_time += session.duration
                total_pages += session.pages_read
                if session.reading_speed:
                    speeds.append(session.reading_speed)
        
        self.total_reading_time = total_time
        self.total_pages_read = total_pages
        
        # Velocidade média de leitura
        if speeds:
            self.average_reading_speed = sum(speeds) / len(speeds)
        
        # Sessão mais longa
        longest = sessions.order_by('-start_time').first()
        if longest and longest.duration:
            self.longest_session = longest.duration
        
        # Livros completados
        self.total_books_completed = sessions.values('book').distinct().count()
        
        self.save()
    
    def __str__(self):
        return f"Estatísticas de {self.user.username}"


class BookAnalytics(models.Model):
    book = models.OneToOneField(Book, on_delete=models.CASCADE)
    total_readers = models.IntegerField(default=0)
    average_reading_time = models.DurationField(default=timedelta())
    completion_rate = models.FloatField(default=0.0)  # porcentagem de conclusão
    average_rating = models.FloatField(default=0.0)
    total_reading_sessions = models.IntegerField(default=0)
    most_read_pages = models.JSONField(default=list)  # páginas mais lidas
    reading_patterns = models.JSONField(default=dict)  # padrões de leitura por hora/dia
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Book Analytics"
        verbose_name_plural = "Book Analytics"
    
    def update_analytics(self):
        """Atualiza as análises do livro baseadas nas sessões"""
        sessions = ReadingSession.objects.filter(book=self.book, end_time__isnull=False)
        
        # Total de leitores únicos
        self.total_readers = sessions.values('user').distinct().count()
        
        # Total de sessões
        self.total_reading_sessions = sessions.count()
        
        # Tempo médio de leitura
        if sessions.exists():
            total_time = sum([s.duration.total_seconds() for s in sessions if s.duration], 0)
            if total_time > 0:
                self.average_reading_time = timedelta(seconds=total_time / sessions.count())
        
        # Taxa de conclusão (simplificada)
        completed_sessions = sessions.filter(pages_read__gte=self.book.total_pages * 0.9)
        if sessions.exists():
            self.completion_rate = (completed_sessions.count() / sessions.count()) * 100
        
        self.save()
    
    def __str__(self):
        return f"Analytics - {self.book.title}"


class ReadingGoal(models.Model):
    GOAL_TYPES = [
        ('daily_pages', 'Páginas por Dia'),
        ('daily_time', 'Tempo por Dia'),
        ('weekly_books', 'Livros por Semana'),
        ('monthly_books', 'Livros por Mês'),
        ('yearly_books', 'Livros por Ano'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Ativa'),
        ('completed', 'Concluída'),
        ('paused', 'Pausada'),
        ('failed', 'Falhada'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPES)
    target_value = models.IntegerField()  # valor alvo (páginas, minutos, livros)
    current_progress = models.IntegerField(default=0)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    @property
    def progress_percentage(self):
        if self.target_value > 0:
            return min((self.current_progress / self.target_value) * 100, 100)
        return 0
    
    @property
    def is_completed(self):
        return self.current_progress >= self.target_value
    
    @property
    def days_remaining(self):
        today = timezone.now().date()
        if self.end_date > today:
            return (self.end_date - today).days
        return 0
    
    def update_progress(self):
        """Atualiza o progresso da meta baseado nas sessões de leitura"""
        today = timezone.now().date()
        
        if self.goal_type == 'daily_pages':
            # Páginas lidas hoje
            sessions_today = ReadingSession.objects.filter(
                user=self.user,
                start_time__date=today,
                end_time__isnull=False
            )
            self.current_progress = sum(s.pages_read for s in sessions_today)
            
        elif self.goal_type == 'daily_time':
            # Tempo lido hoje (em minutos)
            sessions_today = ReadingSession.objects.filter(
                user=self.user,
                start_time__date=today,
                end_time__isnull=False
            )
            total_minutes = sum(s.duration_minutes for s in sessions_today)
            self.current_progress = int(total_minutes)
            
        elif self.goal_type in ['weekly_books', 'monthly_books', 'yearly_books']:
            # Livros completados no período
            sessions_period = ReadingSession.objects.filter(
                user=self.user,
                start_time__date__gte=self.start_date,
                start_time__date__lte=self.end_date,
                end_time__isnull=False
            )
            # Simplificado: considera livros com mais de 80% das páginas lidas
            completed_books = set()
            for session in sessions_period:
                if session.pages_read >= session.book.total_pages * 0.8:
                    completed_books.add(session.book.id)
            self.current_progress = len(completed_books)
        
        # Atualiza status
        if self.is_completed:
            self.status = 'completed'
        elif timezone.now().date() > self.end_date and not self.is_completed:
            self.status = 'failed'
        
        self.save()
    
    def __str__(self):
        return f"{self.user.username} - {self.get_goal_type_display()}: {self.current_progress}/{self.target_value}"