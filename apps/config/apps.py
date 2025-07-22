from django.apps import AppConfig


class ConfigConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.config'
    label = 'config'
    verbose_name = "Configurações e Administração"

    def ready(self):
        """Importa signals quando o app estiver pronto"""
        import apps.config.signals
