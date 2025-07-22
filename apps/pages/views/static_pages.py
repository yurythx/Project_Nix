from django.shortcuts import render
from django.views import View

class AboutView(View):
    """View para página Sobre"""
    template_name = 'pages/about.html'
    
    def get(self, request):
        """Exibe página sobre"""
        context = {
            'meta_title': 'Sobre Nós',
            'meta_description': 'Conheça mais sobre nossa empresa e nossa missão',
        }
        return render(request, self.template_name, context)





class PrivacyView(View):
    """View para política de privacidade"""
    template_name = 'pages/privacy.html'
    
    def get(self, request):
        """Exibe política de privacidade"""
        context = {
            'meta_title': 'Política de Privacidade',
            'meta_description': 'Nossa política de privacidade e proteção de dados',
        }
        return render(request, self.template_name, context)


class TermsView(View):
    """View para termos de uso"""
    template_name = 'pages/terms.html'
    
    def get(self, request):
        """Exibe termos de uso"""
        context = {
            'meta_title': 'Termos de Uso',
            'meta_description': 'Termos e condições de uso do site',
        }
        return render(request, self.template_name, context)
