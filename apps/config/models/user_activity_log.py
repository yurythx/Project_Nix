from django.db import models
from django.conf import settings

class UserActivityLog(models.Model):
    """Modelo para logs de atividade dos usuários"""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user} - {self.action} @ {self.timestamp}"

    class Meta:
        verbose_name = 'log de atividade'
        verbose_name_plural = 'logs de atividade'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
        ]
