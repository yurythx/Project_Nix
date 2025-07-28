from django.forms.widgets import Input
from django.utils.translation import ngettext
from django.utils.html import format_html
from django.template.loader import render_to_string
from django.forms.utils import flatatt
from django.utils.safestring import mark_safe
from django.forms.renderers import get_default_renderer

class MultipleFileInput(Input):
    """
    Widget personalizado para permitir upload de múltiplos arquivos e pastas.
    """
    input_type = 'file'
    template_name = 'mangas/widgets/multiple_file_input.html'
    needs_multipart_form = True
    
    def __init__(self, attrs=None):
        default_attrs = {
            'multiple': True,
            'webkitdirectory': 'true',  # Para Chrome/Edge
            'directory': 'true',        # Para outros navegadores
            'class': 'file-input',
        }
        
        if attrs:
            default_attrs.update(attrs)
            
        super().__init__(default_attrs)
    
    def value_from_datadict(self, data, files, name):
        """
        Retorna uma lista de arquivos do campo de formulário.
        """
        if hasattr(files, 'getlist'):
            return files.getlist(name) or None
        return files.get(name)
    
    def format_value(self, value):
        """
        Retorna os arquivos atuais para exibição no formulário.
        """
        if value is None or value == '':
            return []
        return value if isinstance(value, (list, tuple)) else [value]
    
    def get_context(self, name, value, attrs):
        """
        Retorna o contexto para o template do widget.
        """
        context = super().get_context(name, value, attrs)
        context['widget']['value'] = self.format_value(value)
        context['widget']['attrs'] = self.build_attrs(self.attrs, attrs)
        context['widget']['attrs']['id'] = self.attrs.get('id', f'id_{name}')
        context['widget']['name'] = name
        context['widget']['attrs']['multiple'] = True
        context['widget']['attrs']['webkitdirectory'] = 'true'
        context['widget']['attrs']['directory'] = 'true'
        return context
    
    def render(self, name, value, attrs=None, renderer=None):
        """
        Renderiza o widget.
        """
        context = self.get_context(name, value, attrs or {})
        return render_to_string(self.template_name, context)
