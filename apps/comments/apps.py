from django.apps import AppConfig


class CommentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.comments'
    verbose_name = 'Sistema de Comentários'
    
    def ready(self):
        """Importa signals quando o app está pronto"""
        # import apps.comments.signals  # Temporariamente comentado devido a NotificationService abstrata
        pass