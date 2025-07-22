from django import forms
from apps.audiobooks.models import Audiobook

class AudiobookForm(forms.ModelForm):
    class Meta:
        model = Audiobook
        fields = ['title', 'author', 'narrator', 'description', 'published_date', 
                 'duration', 'cover_image', 'audio_file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título do audiolivro'}),
            'author': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do autor'}),
            'narrator': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do narrador'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Descrição do audiolivro'}),
            'published_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'duration': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'cover_image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'audio_file': forms.FileInput(attrs={'class': 'form-control', 'accept': 'audio/*'}),
        }
        labels = {
            'title': 'Título',
            'author': 'Autor',
            'narrator': 'Narrador',
            'description': 'Descrição',
            'published_date': 'Data de Publicação',
            'duration': 'Duração',
            'cover_image': 'Capa',
            'audio_file': 'Arquivo de Áudio',
        }
