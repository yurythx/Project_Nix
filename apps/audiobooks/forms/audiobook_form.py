from django import forms
from django.utils.translation import gettext_lazy as _
from apps.audiobooks.models import VideoAudio


class VideoAudioForm(forms.ModelForm):
    """Formulário para adicionar ou editar um vídeo como áudio livro"""
    
    class Meta:
        model = VideoAudio
        fields = [
            'title', 'author', 'narrator', 'description', 'published_date',
            'duration', 'thumbnail', 'video_file', 'external_url', 'category',
            'is_featured', 'is_public'
        ]
        
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Título do vídeo')
            }),
            'author': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Autor/Criador')
            }),
            'narrator': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Narrador/Apresentador (opcional)')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': _('Descrição detalhada do conteúdo')
            }),
            'published_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'duration': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
                'step': '1'
            }),
            'thumbnail': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'data-preview': '#thumbnail-preview'
            }),
            'video_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'video/*,.mp4,.webm,.ogg',
                'data-max-size': '500MB'
            }),
            'external_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.youtube.com/watch?v=...',
                'data-video-provider': ''
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
                'data-choices': 'data-choices',
                'data-choices-removeItem': 'true'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'role': 'switch'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'role': 'switch'
            }),
        }
        
        help_texts = {
            'external_url': _('Link para vídeo externo (YouTube, Vimeo, etc.)'),
            'video_file': _('Formatos suportados: MP4, WebM, OGG. Tamanho máximo: 500MB'),
            'duration': _('Duração no formato HH:MM:SS')
        }

    def clean(self):
        cleaned_data = super().clean()
        video_file = cleaned_data.get('video_file')
        external_url = cleaned_data.get('external_url')
        
        # Garante que pelo menos um dos campos (arquivo ou URL) seja fornecido
        if not (video_file or external_url):
            raise forms.ValidationError(
                _('Você deve fornecer um arquivo de vídeo ou uma URL externa.')
            )
            
        # Se ambos forem fornecidos, prioriza o arquivo
        if video_file and external_url:
            cleaned_data['external_url'] = ''
            
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Se for um novo vídeo ou o arquivo foi alterado
        if not instance.pk or 'video_file' in self.changed_data:
            # Aqui você pode adicionar lógica para extrair metadados do vídeo
            # como duração, resolução, etc.
            pass
            
        if commit:
            instance.save()
            self.save_m2m()
            
        return instance
