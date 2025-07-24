"""
Service para processamento de conteúdo de artigos
Implementa interface IContentProcessorService seguindo princípios SOLID
"""
import re
from typing import Optional
from django.utils.html import strip_tags

from apps.articles.interfaces.services import IContentProcessorService


class ContentProcessorService(IContentProcessorService):
    """
    Service responsável por processar e limpar conteúdo de artigos

    Princípios SOLID aplicados:
    - Single Responsibility: Apenas processa conteúdo
    - Open/Closed: Extensível para novos tipos de processamento
    - Liskov Substitution: Implementa interface IContentProcessorService
    - Interface Segregation: Interface específica para processamento
    - Dependency Inversion: Implementa abstração
    """

    def __init__(self):
        """Inicializa o service com configurações padrão"""
        # Elementos que devem ser completamente removidos
        self.elements_to_remove = [
            'article',
            'header',
            'footer',
            'nav',
            'aside'
        ]

        # Classes que indicam elementos problemáticos
        self.problematic_classes = [
            'widget-produto',
            'widget',
            'achados',
            'block-before-content',
            'by',
            'authors-img',
            'author',
            'time',
            'flipboard-subtitle',
            'olho',
            'single-grid',
            'article-header',
            'article-content',
            'entry',
            'grid8',
            'oferta',
            'widget-header',
            'widget-info',
            'pros-cons',
            'btns',
            'widget-footer',
            'social'
        ]

        # Atributos que devem ser removidos
        self.unwanted_attributes = [
            'class',
            'id',
            'style',
            'data-.*',
            'target',
            'rel',
            'title'
        ]
    
    def clean_content(self, content: str) -> str:
        """
        Limpa o conteúdo removendo elementos problemáticos

        Args:
            content: Conteúdo HTML bruto

        Returns:
            Conteúdo HTML limpo
        """
        if not content:
            return ""

        # Passo 1: Remove elementos estruturais problemáticos
        cleaned_content = self._remove_structural_elements(content)

        # Passo 2: Remove divs com classes problemáticas
        cleaned_content = self._remove_problematic_divs(cleaned_content)

        # Passo 3: Remove atributos desnecessários
        cleaned_content = self._remove_unwanted_attributes(cleaned_content)

        # Passo 4: Extrai apenas o conteúdo principal
        cleaned_content = self._extract_main_content(cleaned_content)

        # Passo 5: Limpa espaços e tags vazias
        cleaned_content = self._clean_whitespace_and_empty_tags(cleaned_content)

        return cleaned_content.strip()
    
    def extract_excerpt(self, content: str, max_length: int = 160) -> str:
        """
        Extrai um excerpt limpo do conteúdo

        Args:
            content: Conteúdo HTML
            max_length: Tamanho máximo do excerpt

        Returns:
            Excerpt limpo sem HTML
        """
        if not content:
            return ""

        # Remove todo HTML
        clean_text = strip_tags(content)

        # Remove quebras de linha e espaços extras
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()

        # Trunca se necessário
        if len(clean_text) > max_length:
            clean_text = clean_text[:max_length].rsplit(' ', 1)[0] + '...'

        return clean_text
    
    def _remove_structural_elements(self, content: str) -> str:
        """Remove elementos estruturais problemáticos"""
        for element in self.elements_to_remove:
            # Remove elementos completos com conteúdo
            pattern = f'<{element}[^>]*>.*?</{element}>'
            content = re.sub(pattern, '', content, flags=re.DOTALL | re.IGNORECASE)
        return content

    def _remove_problematic_divs(self, content: str) -> str:
        """Remove divs com classes problemáticas"""
        for class_name in self.problematic_classes:
            # Remove divs com essas classes
            pattern = f'<div[^>]*class="[^"]*{class_name}[^"]*"[^>]*>.*?</div>'
            content = re.sub(pattern, '', content, flags=re.DOTALL | re.IGNORECASE)
        return content

    def _remove_unwanted_attributes(self, content: str) -> str:
        """Remove atributos HTML desnecessários"""
        for attr in self.unwanted_attributes:
            if attr == 'data-.*':
                # Remove todos os atributos data-*
                content = re.sub(r'data-[^=]*="[^"]*"', '', content)
            else:
                # Remove atributo específico
                content = re.sub(f'{attr}="[^"]*"', '', content)
        return content

    def _extract_main_content(self, content: str) -> str:
        """Extrai apenas o conteúdo principal (parágrafos, títulos, imagens)"""
        # Padrão para extrair apenas elementos de conteúdo
        content_pattern = r'(<h[1-6][^>]*>.*?</h[1-6]>|<p[^>]*>.*?</p>|<img[^>]*>|<figure[^>]*>.*?</figure>|<iframe[^>]*>.*?</iframe>|<ul[^>]*>.*?</ul>|<ol[^>]*>.*?</ol>|<blockquote[^>]*>.*?</blockquote>)'

        matches = re.findall(content_pattern, content, flags=re.DOTALL | re.IGNORECASE)
        return '\n'.join(matches)

    def _clean_whitespace_and_empty_tags(self, content: str) -> str:
        """Limpa espaços extras e tags vazias"""
        # Remove espaços extras entre tags
        content = re.sub(r'>\s+<', '><', content)

        # Remove tags vazias (exceto img, br, hr, iframe)
        content = re.sub(r'<(?!img|br|hr|iframe)([^>]+)>\s*</\1>', '', content)

        # Normaliza espaços
        content = re.sub(r'\s+', ' ', content)

        # Remove linhas vazias
        content = re.sub(r'\n\s*\n', '\n', content)

        return content
    
    def process_for_display(self, content: str) -> str:
        """
        Processa conteúdo para exibição otimizada

        Args:
            content: Conteúdo HTML

        Returns:
            Conteúdo formatado para exibição
        """
        if not content:
            return ""

        # Aplica limpeza completa
        formatted_content = self.clean_content(content)

        # Adiciona classes Bootstrap para melhor formatação
        formatted_content = self._add_bootstrap_classes(formatted_content)

        return formatted_content
    
    def _add_bootstrap_classes(self, content: str) -> str:
        """Adiciona classes Bootstrap para melhor formatação"""
        # Adiciona classes para imagens
        content = re.sub(r'<img([^>]*)>', r'<img\1 class="img-fluid rounded">', content)
        
        # Adiciona classes para tabelas
        content = re.sub(r'<table([^>]*)>', r'<table\1 class="table table-striped">', content)
        
        # Adiciona classes para blockquotes
        content = re.sub(r'<blockquote([^>]*)>', r'<blockquote\1 class="blockquote">', content)
        
        return content


class ArticleContentProcessor:
    """
    Facade para processamento de conteúdo de artigos
    Implementa o padrão Facade para simplificar o uso do ContentProcessorService
    """
    
    def __init__(self, processor_service: Optional[ContentProcessorService] = None):
        """
        Inicializa o processor com injeção de dependência
        
        Args:
            processor_service: Service de processamento (opcional)
        """
        self.processor = processor_service or ContentProcessorService()
    
    def process_article_content(self, content: str) -> str:
        """
        Processa conteúdo de artigo para exibição
        
        Args:
            content: Conteúdo HTML bruto
            
        Returns:
            Conteúdo processado e limpo
        """
        return self.processor.format_for_display(content)
    
    def generate_excerpt(self, content: str, max_length: int = 160) -> str:
        """
        Gera excerpt limpo do conteúdo
        
        Args:
            content: Conteúdo HTML
            max_length: Tamanho máximo
            
        Returns:
            Excerpt limpo
        """
        return self.processor.extract_clean_excerpt(content, max_length)
