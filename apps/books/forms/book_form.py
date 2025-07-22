from django import forms
from apps.books.models.book import Book

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'description', 'published_date', 'cover_image', 'file']
        widgets = {
            'published_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            if not file.name.lower().endswith(('.epub', '.pdf')):
                raise forms.ValidationError('Apenas arquivos EPUB ou PDF são permitidos.')
            if file.size > 20 * 1024 * 1024:
                raise forms.ValidationError('Arquivo muito grande (máx. 20MB).')
        return file 