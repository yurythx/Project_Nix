from django import forms
from django.utils.translation import gettext_lazy as _
from apps.audiobooks.models import VideoAudio


class VideoAudioForm(forms.ModelForm):
    """Formulário para adicionar ou editar um vídeo como áudio livro
    
    Princípios SOLID aplicados:
    - Single Responsibility: Responsável apenas pela validação e formatação dos dados do formulário
    - Open/Closed: Extensível via herança
    - Interface Segregation: Expõe apenas os métodos necessários para um formulário
    """
    
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
        """Valida os dados do formulário
        
        Segue o princípio de Single Responsibility ao delegar validações específicas
        para métodos separados.
        """
        cleaned_data = super().clean()
        
        # Valida que pelo menos um meio de vídeo foi fornecido
        self._validate_video_source(cleaned_data)
        
        # Prioriza o arquivo de vídeo se ambos forem fornecidos
        self._prioritize_video_file(cleaned_data)
        
        # Valida o tamanho do arquivo se fornecido
        self._validate_file_size(cleaned_data)
        
        return cleaned_data
    
    def _validate_video_source(self, cleaned_data):
        """Valida que pelo menos um meio de vídeo (arquivo ou URL) foi fornecido"""
        video_file = cleaned_data.get('video_file')
        external_url = cleaned_data.get('external_url')
        
        if not (video_file or external_url):
            raise forms.ValidationError(
                _('Você deve fornecer um arquivo de vídeo ou uma URL externa.')
            )
    
    def _prioritize_video_file(self, cleaned_data):
        """Prioriza o arquivo de vídeo se ambos (arquivo e URL) forem fornecidos"""
        video_file = cleaned_data.get('video_file')
        external_url = cleaned_data.get('external_url')
        
        if video_file and external_url:
            cleaned_data['external_url'] = ''
    
    def _validate_file_size(self, cleaned_data):
        """Valida o tamanho do arquivo de vídeo se fornecido"""
        video_file = cleaned_data.get('video_file')
        
        if video_file and hasattr(video_file, 'size'):
            # Tamanho máximo: 500MB (em bytes)
            max_size = 500 * 1024 * 1024
            
            if video_file.size > max_size:
                raise forms.ValidationError(
                    _('O arquivo de vídeo excede o tamanho máximo permitido (500MB).')
                )
    
    def save(self, commit=True):
        """Salva o formulário e processa metadados do vídeo se necessário"""
        instance = super().save(commit=False)
        
        # Se for um novo vídeo ou o arquivo foi alterado
        if not instance.pk or 'video_file' in self.changed_data:
            self._process_video_metadata(instance)
            
        if commit:
            instance.save()
            self.save_m2m()
            
        return instance
        
    def _process_video_metadata(self, instance):
        """Processa metadados do vídeo como duração, resolução, etc.
        
        Este método segue o princípio de Single Responsibility ao extrair
        a lógica de processamento de metadados para um método separado.
        """
        if not instance.video_file:
            return
            
        try:
            # Aqui você pode adicionar lógica para extrair metadados do vídeo
            # usando bibliotecas como moviepy, ffmpeg, etc.
            # Exemplo:
            # from moviepy.editor import VideoFileClip
            # clip = VideoFileClip(instance.video_file.path)
            # instance.duration = self._format_duration(clip.duration)
            # clip.close()
            pass
        except Exception as e:
            # Log do erro, mas não interrompe o salvamento
            print(f"Erro ao processar metadados do vídeo: {e}")
            
    def _format_duration(self, seconds):
        """Formata a duração em segundos para o formato HH:MM:SS"""
        import datetime
        return str(datetime.timedelta(seconds=int(seconds)))
