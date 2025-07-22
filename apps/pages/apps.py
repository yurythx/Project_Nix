from django.apps import AppConfig


class PagesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.pages'
    label = 'pages'
    verbose_name = "Páginas da Aplicação"

    def ready(self):
        """Importa signals quando o app estiver pronto"""
        import apps.pages.signals
