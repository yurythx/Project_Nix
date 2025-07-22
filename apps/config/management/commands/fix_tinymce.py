from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
import os
import shutil
import urllib.request
import zipfile
from pathlib import Path

class Command(BaseCommand):
    help = 'Corrige problemas do TinyMCE em produção'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--download-only',
            action='store_true',
            help='Apenas baixa o TinyMCE sem fazer outras correções',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força o download mesmo se já existir',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🦟 CORREÇÃO DO TINYMCE EM PRODUÇÃO')
        )
        self.stdout.write('=' * 50)
        
        download_only = options.get('download_only', False)
        force = options.get('force', False)
        
        if download_only:
            self.download_tinymce(force)
            return
        
        # Executar todas as correções
        self.download_tinymce(force)
        self.create_tinymce_files()
        self.update_template()
        self.collect_static_files()
        self.test_tinymce()
    
    def download_tinymce(self, force=False):
        """Baixa o TinyMCE"""
        self.stdout.write('📥 Baixando TinyMCE...')
        
        tinymce_path = Path(settings.STATIC_ROOT) / 'tinymce'
        
        if tinymce_path.exists() and not force:
            self.stdout.write(self.style.WARNING('TinyMCE já existe. Use --force para baixar novamente.'))
            return True
        
        try:
            # URL do TinyMCE
            tinymce_url = "https://download.tiny.cloud/tinymce/community/tinymce_6.8.3.zip"
            zip_path = "tinymce_temp.zip"
            
            # Baixar arquivo
            self.stdout.write(f'Baixando de: {tinymce_url}')
            urllib.request.urlretrieve(tinymce_url, zip_path)
            
            # Extrair arquivo
            self.stdout.write('📂 Extraindo arquivos...')
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall("temp_tinymce")
            
            # Mover para pasta static
            temp_path = Path("temp_tinymce/tinymce")
            if temp_path.exists():
                if tinymce_path.exists():
                    shutil.rmtree(tinymce_path)
                shutil.move(str(temp_path), str(tinymce_path))
                self.stdout.write(self.style.SUCCESS(f'✅ TinyMCE movido para {tinymce_path}'))
            
            # Limpar arquivos temporários
            if os.path.exists("temp_tinymce"):
                shutil.rmtree("temp_tinymce")
            if os.path.exists(zip_path):
                os.remove(zip_path)
            
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao baixar TinyMCE: {e}'))
            return False
    
    def create_tinymce_files(self):
        """Cria arquivos necessários do TinyMCE"""
        self.stdout.write('📝 Criando arquivos do TinyMCE...')
        
        # Criar diretórios se não existirem
        os.makedirs(settings.STATIC_ROOT / 'js', exist_ok=True)
        os.makedirs(settings.STATIC_ROOT / 'css', exist_ok=True)
        
        # Criar arquivo de inicialização
        init_content = '''/**
 * TinyMCE Initialization Script
 * Versão otimizada para produção
 */

(function() {
    'use strict';
    
    // Configuração base do TinyMCE
    const tinymceConfig = {
        selector: 'textarea.tinymce, .tinymce',
        height: 500,
        width: '100%',
        skin: 'oxide',
        content_css: '/static/css/tinymce-content.css',
        plugins: [
            'advlist', 'autolink', 'lists', 'link', 'image', 'charmap', 'preview',
            'anchor', 'searchreplace', 'visualblocks', 'code', 'insertdatetime',
            'media', 'table', 'wordcount', 'emoticons', 'nonbreaking', 'directionality'
        ].join(' '),
        toolbar: [
            'undo redo | bold italic underline strikethrough | fontselect fontsizeselect formatselect',
            'alignleft aligncenter alignright alignjustify | outdent indent | numlist bullist',
            'forecolor backcolor removeformat | charmap emoticons',
            'visualblocks visualchars | nonbreaking anchor | link unlink | image media',
            'table | code | preview | help'
        ].join(' | '),
        menubar: true,
        statusbar: true,
        branding: false,
        promotion: false,
        language: 'pt_BR',
        paste_data_images: true,
        paste_as_text: false,
        paste_auto_cleanup_on_paste: false,
        paste_remove_styles: false,
        paste_remove_styles_if_webkit: false,
        paste_strip_class_attributes: 'none',
        paste_enable_default_filters: false,
        paste_word_valid_elements: '*[*]',
        paste_retain_style_properties: 'color background-color font-size font-family font-weight text-decoration',
        paste_merge_formats: true,
        paste_convert_word_fake_lists: false,
        paste_filter_drop: false,
        paste_webkit_styles: 'color background-color font-size font-family',
        verify_html: false,
        cleanup: false,
        cleanup_on_startup: false,
        forced_root_block: 'p',
        force_br_newlines: false,
        force_p_newlines: true,
        remove_linebreaks: false,
        convert_newlines_to_brs: false,
        remove_redundant_brs: false,
        remove_trailing_brs: false,
        entity_encoding: 'raw',
        encoding: 'xml',
        element_format: 'html',
        schema: 'html5',
        valid_children: '+body[style]',
        extended_valid_elements: 'span[*],div[*],p[*],br[*],hr[*],h1[*],h2[*],h3[*],h4[*],h5[*],h6[*],ul[*],ol[*],li[*],a[*],img[*],video[*],iframe[*],table[*],tr[*],td[*],th[*],thead[*],tbody[*],tfoot[*],caption[*],colgroup[*],col[*],blockquote[*],pre[*],code[*],em[*],strong[*],b[*],i[*],u[*],s[*],del[*],ins[*],mark[*],small[*],sub[*],sup[*],cite[*],q[*],abbr[*],acronym[*],dfn[*],kbd[*],samp[*],var[*],time[*]',
        invalid_elements: 'script,object,embed,form,input,textarea,select,button,label,fieldset,legend,frame,frameset,noframes,applet,basefont,bgsound,link,meta,style,title,xmp,plaintext,listing,marquee,blink,isindex,dir,menu,center,font,strike,tt,u,big,small,spacer,layers,ilayer,base,basefont,center,font,strike,tt,u,big,small,spacer,layers,ilayer',
        valid_attributes: '*[*]',
        invalid_attributes: 'on*',
        media_live_embeds: true,
        media_alt_source: false,
        media_poster: false,
        media_dimensions: false,
        media_url_resolver: 'function(data, resolve, reject) { resolve(data); }',
        media_scripts: [{'filter': 'iframe', 'width': 300, 'height': 150}],
        fullscreen_native: true,
        resize: false,
        elementpath: false,
        toolbar_mode: 'sliding',
        toolbar_sticky: true,
        relative_urls: false,
        remove_script_host: false,
        convert_urls: true,
        setup: function(editor) {
            console.log('TinyMCE editor setup:', editor.id);
        },
        init_instance_callback: function(editor) {
            console.log('TinyMCE editor initialized:', editor.id);
            window.tinyMCEInitialized = true;
        }
    };
    
    // Função para inicializar TinyMCE
    function initTinyMCE() {
        if (typeof tinymce === 'undefined') {
            console.log('TinyMCE not loaded yet, retrying...');
            setTimeout(initTinyMCE, 500);
            return;
        }
        
        if (window.tinyMCEInitialized) {
            console.log('TinyMCE already initialized');
            return;
        }
        
        console.log('Initializing TinyMCE...');
        tinymce.init(tinymceConfig);
    }
    
    // Inicialização quando DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initTinyMCE);
    } else {
        initTinyMCE();
    }
    
    // Reinicializar quando tema mudar
    window.addEventListener('themeChanged', function() {
        console.log('Theme changed, reinitializing TinyMCE...');
        if (window.tinymce && tinymce.editors) {
            tinymce.editors.forEach(function(editor) { 
                editor.remove(); 
            });
        }
        window.tinyMCEInitialized = false;
        setTimeout(initTinyMCE, 400);
    });
    
})();
'''
        
        with open(settings.STATIC_ROOT / 'js' / 'tinymce-init.js', 'w', encoding='utf-8') as f:
            f.write(init_content)
        
        # Criar CSS
        css_content = '''/* TinyMCE Content CSS */
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 16px;
    line-height: 1.6;
    color: #333;
    background: #fff;
    margin: 0;
    padding: 20px;
}

h1, h2, h3, h4, h5, h6 {
    margin-top: 0;
    margin-bottom: 0.5em;
    font-weight: 600;
    line-height: 1.2;
}

h1 { font-size: 2em; }
h2 { font-size: 1.75em; }
h3 { font-size: 1.5em; }
h4 { font-size: 1.25em; }
h5 { font-size: 1.1em; }
h6 { font-size: 1em; }

p {
    margin-top: 0;
    margin-bottom: 1em;
}

ul, ol {
    margin-top: 0;
    margin-bottom: 1em;
    padding-left: 2em;
}

li {
    margin-bottom: 0.25em;
}

a {
    color: #007bff;
    text-decoration: underline;
}

a:hover {
    color: #0056b3;
    text-decoration: none;
}

img {
    max-width: 100%;
    height: auto;
    border-radius: 4px;
}

table {
    border-collapse: collapse;
    width: 100%;
    margin-bottom: 1em;
}

table, th, td {
    border: 1px solid #ddd;
}

th, td {
    padding: 8px 12px;
    text-align: left;
}

th {
    background-color: #f8f9fa;
    font-weight: 600;
}

blockquote {
    margin: 0 0 1em 0;
    padding: 0.5em 1em;
    border-left: 4px solid #007bff;
    background-color: #f8f9fa;
    font-style: italic;
}

code {
    background-color: #f8f9fa;
    padding: 0.2em 0.4em;
    border-radius: 3px;
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
    font-size: 0.9em;
}

pre {
    background-color: #f8f9fa;
    padding: 1em;
    border-radius: 4px;
    overflow-x: auto;
    margin-bottom: 1em;
}

pre code {
    background: none;
    padding: 0;
}

strong, b { font-weight: 600; }
em, i { font-style: italic; }
u { text-decoration: underline; }
s, del { text-decoration: line-through; }

@media (max-width: 768px) {
    body {
        font-size: 14px;
        padding: 15px;
    }
    
    h1 { font-size: 1.75em; }
    h2 { font-size: 1.5em; }
    h3 { font-size: 1.25em; }
    h4 { font-size: 1.1em; }
    h5 { font-size: 1em; }
    h6 { font-size: 0.9em; }
}
'''
        
        with open(settings.STATIC_ROOT / 'css' / 'tinymce-content.css', 'w', encoding='utf-8') as f:
            f.write(css_content)
        
        self.stdout.write(self.style.SUCCESS('✅ Arquivos do TinyMCE criados'))
    
    def update_template(self):
        """Atualiza o template base"""
        self.stdout.write('📄 Atualizando template base...')
        
        base_template_path = 'apps/pages/templates/base.html'
        
        if not os.path.exists(base_template_path):
            self.stdout.write(self.style.ERROR(f'Template base não encontrado: {base_template_path}'))
            return False
        
        try:
            with open(base_template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verificar se TinyMCE já está incluído
            if 'tinymce.min.js' in content:
                self.stdout.write(self.style.WARNING('TinyMCE já está incluído no template'))
                return True
            
            # Encontrar posição para inserir TinyMCE
            head_end = content.find('</head>')
            if head_end == -1:
                self.stdout.write(self.style.ERROR('Não foi possível encontrar </head> no template'))
                return False
            
            # Scripts do TinyMCE para inserir
            tinymce_scripts = '''
    <!-- TinyMCE -->
    <script src="/static/tinymce/tinymce.min.js"></script>
    <script src="/static/js/tinymce-init.js"></script>
'''
            
            # Inserir scripts
            new_content = content[:head_end] + tinymce_scripts + content[head_end:]
            
            # Salvar arquivo
            with open(base_template_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            self.stdout.write(self.style.SUCCESS('✅ Template base atualizado'))
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro ao atualizar template: {e}'))
            return False
    
    def collect_static_files(self):
        """Coleta arquivos estáticos"""
        self.stdout.write('📦 Coletando arquivos estáticos...')
        
        try:
            call_command('collectstatic', '--noinput', '--clear')
            self.stdout.write(self.style.SUCCESS('✅ Arquivos estáticos coletados'))
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro ao coletar arquivos estáticos: {e}'))
            return False
    
    def test_tinymce(self):
        """Testa se o TinyMCE está funcionando"""
        self.stdout.write('🧪 Testando TinyMCE...')
        
        try:
            # Verificar se os arquivos existem
            files_to_check = [
                settings.STATIC_ROOT / 'tinymce' / 'tinymce.min.js',
                settings.STATIC_ROOT / 'js' / 'tinymce-init.js',
                settings.STATIC_ROOT / 'css' / 'tinymce-content.css'
            ]
            
            for file_path in files_to_check:
                if file_path.exists():
                    self.stdout.write(f'✅ {file_path}')
                else:
                    self.stdout.write(self.style.ERROR(f'❌ {file_path} não encontrado'))
                    return False
            
            self.stdout.write(self.style.SUCCESS('✅ Todos os arquivos do TinyMCE estão presentes'))
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro no teste: {e}'))
            return False 