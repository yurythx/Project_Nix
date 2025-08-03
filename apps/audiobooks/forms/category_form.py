from django import forms
from django.utils.translation import gettext_lazy as _

from apps.audiobooks.models.category import Category

class CategoryForm(forms.ModelForm):
    """
    Formulário para adicionar ou editar uma categoria
    
    Princípios SOLID aplicados:
    - Single Responsibility: Responsável apenas pela validação e formatação dos dados do formulário
    - Open/Closed: Extensível via herança
    """
    
    class Meta:
        model = Category
        fields = ['name', 'description', 'icon', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Nome da categoria')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Descrição da categoria')
            }),
            'icon': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Nome do ícone FontAwesome (ex: fa-podcast)')
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise forms.ValidationError(_('O nome da categoria é obrigatório.'))
        
        # Verifica se já existe uma categoria com este nome (exceto a atual em caso de edição)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            # Estamos editando uma categoria existente
            if Category.objects.filter(name=name).exclude(pk=instance.pk).exists():
                raise forms.ValidationError(_('Já existe uma categoria com este nome.'))
        else:
            # Estamos criando uma nova categoria
            if Category.objects.filter(name=name).exists():
                raise forms.ValidationError(_('Já existe uma categoria com este nome.'))
        
        return name