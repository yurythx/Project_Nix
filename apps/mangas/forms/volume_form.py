from django import forms
from django.utils.translation import gettext_lazy as _
from apps.mangas.models.volume import Volume

class VolumeForm(forms.ModelForm):
    """Formulário para criação e edição de volumes de mangá."""
    class Meta:
        model = Volume
        fields = ['number', 'title', 'cover_image', 'is_published']
        labels = {
            'number': _('Número do Volume'),
            'title': _('Título (opcional)'),
            'cover_image': _('Capa do Volume'),
            'is_published': _('Publicado?'),
        }
        help_texts = {
            'number': _('Número sequencial do volume (ex: 1, 2, 3, etc.)'),
            'title': _('Título opcional para o volume (deixe em branco para usar apenas o número)'),
            'cover_image': _('Imagem de capa do volume (opcional)'),
            'is_published': _('Selecione para tornar este volume visível publicamente'),
        }
        widgets = {
            'number': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adiciona classes CSS aos campos
        for field_name, field in self.fields.items():
            if field_name != 'is_published':
                field.widget.attrs.update({'class': 'form-control'})
    
    def clean_number(self):
        """Valida se o número do volume é único para o mangá."""
        number = self.cleaned_data.get('number')
        manga = self.instance.manga if hasattr(self.instance, 'manga') else None
        
        if manga and 'manga' in self.data:
            # Verifica se já existe um volume com o mesmo número para este mangá
            queryset = Volume.objects.filter(manga=manga, number=number)
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise forms.ValidationError(
                    _('Já existe um volume com este número para este mangá.')
                )
        
        return number
