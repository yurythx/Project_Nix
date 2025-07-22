from django import forms
from apps.mangas.models.manga import Manga, Capitulo, Pagina

class MangaForm(forms.ModelForm):
    class Meta:
        model = Manga
        fields = ['title', 'author', 'description', 'cover_image']

class CapituloForm(forms.ModelForm):
    class Meta:
        model = Capitulo
        fields = ['number', 'title']

class PaginaForm(forms.ModelForm):
    class Meta:
        model = Pagina
        fields = ['number', 'image']

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            ext = image.name.lower().split('.')[-1]
            if ext not in ['jpg', 'jpeg', 'png', 'webp']:
                raise forms.ValidationError('Apenas imagens JPG, PNG ou WEBP são permitidas.')
            if image.size > 10 * 1024 * 1024:
                raise forms.ValidationError('Imagem muito grande (máx. 10MB).')
        return image 