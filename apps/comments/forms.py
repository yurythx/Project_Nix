from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags
from django.contrib.contenttypes.models import ContentType
import re

from .models import Comment, CommentModeration, NotificationPreference

User = get_user_model()


class CommentForm(forms.ModelForm):
    """
    Formulário para criação e edição de comentários
    """
    
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Escreva seu comentário...',
            'maxlength': 2000,
        }),
        label='Comentário',
        help_text='Máximo de 2000 caracteres',
        max_length=2000,
        min_length=3
    )
    
    class Meta:
        model = Comment
        fields = ['content']
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.content_object = kwargs.pop('content_object', None)
        self.parent = kwargs.pop('parent', None)
        super().__init__(*args, **kwargs)
    
    def clean_content(self):
        """Valida e limpa o conteúdo do comentário"""
        content = self.cleaned_data.get('content', '').strip()
        
        if not content:
            raise ValidationError('Comentário não pode estar vazio')
        
        if len(content) < 3:
            raise ValidationError('Comentário deve ter pelo menos 3 caracteres')
        
        if len(content) > 2000:
            raise ValidationError('Comentário não pode ter mais de 2000 caracteres')
        
        # Remove tags HTML perigosas
        content = strip_tags(content)
        
        # Verifica spam básico
        if self._is_potential_spam(content):
            raise ValidationError('Comentário parece ser spam')
        
        return content
    
    def _is_potential_spam(self, content):
        """Detecção básica de spam"""
        spam_patterns = [
            r'\b(viagra|cialis|casino|poker)\b',
            r'\b(click here|visit now|buy now)\b',
            r'\b(free money|easy money)\b',
        ]
        
        content_lower = content.lower()
        for pattern in spam_patterns:
            if re.search(pattern, content_lower):
                return True
        
        # Verifica repetição excessiva
        words = content_lower.split()
        if len(words) > 5:
            unique_words = set(words)
            if len(unique_words) / len(words) < 0.3:
                return True
        
        return False


class CommentReplyForm(CommentForm):
    """
    Formulário específico para respostas
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].widget.attrs.update({
            'placeholder': 'Escreva sua resposta...',
            'rows': 3,
        })
        self.fields['content'].help_text = 'Resposta ao comentário acima'


class CommentSearchForm(forms.Form):
    """
    Formulário de busca de comentários
    """
    
    query = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar comentários...',
            'autocomplete': 'off',
        }),
        label='Buscar',
        max_length=200,
        min_length=3,
        required=True
    )
    
    author = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Autor',
        required=False,
        empty_label='Todos os autores'
    )
    
    content_type = forms.ModelChoiceField(
        queryset=ContentType.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Tipo de conteúdo',
        required=False,
        empty_label='Todos os tipos'
    )
    
    date_from = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Data inicial',
        required=False
    )
    
    date_to = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Data final',
        required=False
    )
    
    def clean_query(self):
        """Valida termo de busca"""
        query = self.cleaned_data.get('query', '').strip()
        
        if len(query) < 3:
            raise ValidationError('Termo de busca deve ter pelo menos 3 caracteres')
        
        return query
    
    def clean(self):
        """Validação geral do formulário"""
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise ValidationError('Data inicial deve ser anterior à data final')
        
        return cleaned_data


class CommentReportForm(forms.Form):
    """
    Formulário para reportar comentários
    """
    
    REPORT_REASONS = [
        ('spam', 'Spam'),
        ('harassment', 'Assédio'),
        ('hate_speech', 'Discurso de ódio'),
        ('inappropriate', 'Conteúdo inapropriado'),
        ('off_topic', 'Fora do tópico'),
        ('misinformation', 'Desinformação'),
        ('other', 'Outro'),
    ]
    
    reason = forms.ChoiceField(
        choices=REPORT_REASONS,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Motivo do report',
        required=True
    )
    
    details = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Descreva o problema (opcional)...',
        }),
        label='Detalhes',
        required=False,
        max_length=500
    )
    
    def clean_details(self):
        """Valida detalhes do report"""
        details = self.cleaned_data.get('details', '').strip()
        
        if self.cleaned_data.get('reason') == 'other' and not details:
            raise ValidationError('Detalhes são obrigatórios quando o motivo é "Outro"')
        
        return details


class ModerationActionForm(forms.Form):
    """
    Formulário para ações de moderação
    """
    
    ACTION_CHOICES = [
        ('approve', 'Aprovar'),
        ('reject', 'Rejeitar'),
        ('spam', 'Marcar como spam'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Ação',
        required=True
    )
    
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Motivo da ação (opcional)...',
        }),
        label='Motivo',
        required=False,
        max_length=500
    )
    
    notify_user = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Notificar usuário',
        required=False,
        initial=True
    )


class BulkModerationForm(forms.Form):
    """
    Formulário para moderação em massa
    """
    
    comment_ids = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )
    
    action = forms.ChoiceField(
        choices=ModerationActionForm.ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Ação',
        required=True
    )
    
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Motivo da ação...',
        }),
        label='Motivo',
        required=True,
        max_length=500
    )
    
    def clean_comment_ids(self):
        """Valida IDs dos comentários"""
        comment_ids_str = self.cleaned_data.get('comment_ids', '')
        
        try:
            comment_ids = [int(id_str) for id_str in comment_ids_str.split(',') if id_str.strip()]
        except ValueError:
            raise ValidationError('IDs de comentários inválidos')
        
        if not comment_ids:
            raise ValidationError('Nenhum comentário selecionado')
        
        if len(comment_ids) > 100:
            raise ValidationError('Máximo de 100 comentários por vez')
        
        return comment_ids


class CommentModerationConfigForm(forms.ModelForm):
    """
    Formulário para configuração de moderação
    """
    
    class Meta:
        model = CommentModeration
        fields = [
            'moderation_type',
            'auto_approve_trusted_users',
            'require_email_verification',
            'max_comment_length',
            'min_comment_length',
            'enable_spam_filter',
            'blocked_words',
            'blocked_ips',
            'max_comments_per_hour',
            'max_comments_per_day',
            'notify_moderators',
            'notify_authors',
            'is_active',
        ]
        widgets = {
            'moderation_type': forms.Select(attrs={'class': 'form-control'}),
            'auto_approve_trusted_users': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'require_email_verification': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'max_comment_length': forms.NumberInput(attrs={'class': 'form-control'}),
            'min_comment_length': forms.NumberInput(attrs={'class': 'form-control'}),
            'enable_spam_filter': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'blocked_words': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Uma palavra por linha...',
            }),
            'blocked_ips': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Um IP por linha...',
            }),
            'max_comments_per_hour': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_comments_per_day': forms.NumberInput(attrs={'class': 'form-control'}),
            'notify_moderators': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notify_authors': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class NotificationPreferencesForm(forms.ModelForm):
    """
    Formulário para preferências de notificação
    """
    
    class Meta:
        model = NotificationPreference
        fields = [
            'email_on_reply',
            'email_on_mention',
            'email_on_like',
            'email_on_moderation',
            'realtime_on_reply',
            'realtime_on_mention',
            'realtime_on_like',
            'realtime_on_moderation',
            'digest_frequency',
            'quiet_hours_start',
            'quiet_hours_end',
        ]
        widgets = {
            'email_on_reply': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_on_mention': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_on_like': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_on_moderation': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'realtime_on_reply': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'realtime_on_mention': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'realtime_on_like': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'realtime_on_moderation': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'digest_frequency': forms.Select(attrs={'class': 'form-control'}),
            'quiet_hours_start': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'quiet_hours_end': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
        }
    
    def clean(self):
        """Validação geral do formulário"""
        cleaned_data = super().clean()
        quiet_start = cleaned_data.get('quiet_hours_start')
        quiet_end = cleaned_data.get('quiet_hours_end')
        
        if quiet_start and quiet_end and quiet_start >= quiet_end:
            raise ValidationError('Horário de início deve ser anterior ao horário de fim')
        
        return cleaned_data


class CommentFilterForm(forms.Form):
    """
    Formulário para filtrar comentários
    """
    
    STATUS_CHOICES = [
        ('', 'Todos os status'),
        ('pending', 'Pendente'),
        ('approved', 'Aprovado'),
        ('rejected', 'Rejeitado'),
        ('spam', 'Spam'),
        ('deleted', 'Deletado'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Status',
        required=False
    )
    
    author = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Autor',
        required=False,
        empty_label='Todos os autores'
    )
    
    date_from = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Data inicial',
        required=False
    )
    
    date_to = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Data final',
        required=False
    )
    
    has_replies = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Apenas com respostas',
        required=False
    )
    
    is_pinned = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Apenas fixados',
        required=False
    )