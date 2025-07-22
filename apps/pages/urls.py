from django.urls import path
from django.views.generic import TemplateView
from apps.pages.views import (
    HomeView,
    AboutView,
    PrivacyView,
    TermsView,
    PageSearchView,
)

app_name = 'pages'

urlpatterns = [
    # Página inicial
    path('', HomeView.as_view(), name='home'),

    # Páginas estáticas
    path('sobre/', AboutView.as_view(), name='about'),
    path('privacidade/', PrivacyView.as_view(), name='privacy'),
    path('termos/', TermsView.as_view(), name='terms'),

  

    # Páginas dinâmicas
    
    path('busca/', PageSearchView.as_view(), name='search'),

   
]
