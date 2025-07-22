from django.urls import path
from apps.audiobooks.views.audiobook_views import (
    AudiobookListView, AudiobookDetailView, AudiobookCreateView, 
    AudiobookUpdateView, AudiobookDeleteView
)

app_name = 'audiobooks'

urlpatterns = [
    path('', AudiobookListView.as_view(), name='audiobook_list'),
    path('novo/', AudiobookCreateView.as_view(), name='audiobook_create'),
    path('<slug:slug>/', AudiobookDetailView.as_view(), name='audiobook_detail'),
    path('<slug:slug>/editar/', AudiobookUpdateView.as_view(), name='audiobook_edit'),
    path('<slug:slug>/deletar/', AudiobookDeleteView.as_view(), name='audiobook_delete'),
]
