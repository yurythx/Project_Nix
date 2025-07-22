"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from .health_check import health_check, readiness_check, liveness_check
from apps.config.views.setup_wizard_view import setup_redirect

# Importar views de erro personalizadas
from apps.accounts.middleware import handle_403_error, handle_404_error

# URLs principais da aplicação
urlpatterns = [
    # Setup redirect (primeira instalação)
    path('', setup_redirect, name='setup_redirect'),
    
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('config/', include('apps.config.urls')),
    path('artigos/', include('apps.articles.urls')),
    path('tinymce/', include('tinymce.urls')),

    # Health checks
    path('health/', health_check, name='health_check'),
    path('health/ready/', readiness_check, name='readiness_check'),
    path('health/live/', liveness_check, name='liveness_check'),

    # Pages como app principal (DEVE SER O ÚLTIMO devido ao catch-all)
    path('pages/', include('apps.pages.urls')),
]

# Views de erro personalizadas
handler403 = 'apps.accounts.middleware.handle_403_error'
handler404 = 'apps.accounts.middleware.handle_404_error'

# Servir arquivos de mídia (desenvolvimento e produção)
if settings.DEBUG:
    # Em desenvolvimento, usar o servidor de desenvolvimento do Django
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    # Em produção, usar view personalizada para mídia
    urlpatterns += [
        path('media/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}, name='media'),
    ]
