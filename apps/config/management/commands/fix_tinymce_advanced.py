from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
import os
import shutil
from pathlib import Path

class Command(BaseCommand):
    help = 'Corrige problemas avançados do TinyMCE (imagens, vídeos, ferramentas)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--images-only',
            action='store_true',
            help='Apenas corrige problemas de imagem',
        )
        parser.add_argument(
            '--paste-only',
            action='store_true',
            help='Apenas corrige problemas de paste',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🦟 CORREÇÃO AVANÇADA DO TINYMCE')
        )
        self.stdout.write('=' * 50)
        
        images_only = options.get('images_only', False)
        paste_only = options.get('paste_only', False)
        
        if images_only:
            self.fix_image_issues()
            return
        
        if paste_only:
            self.fix_paste_issues()
            return
        
        # Executar todas as correções
        self.fix_image_issues()
        self.fix_paste_issues()
        self.fix_toolbar_issues()
        self.update_settings()
        self.collect_static_files()
        self.test_features()
    
    def fix_image_issues(self):
        """Corrige problemas de imagem"""
        self.stdout.write('🖼️ Corrigindo problemas de imagem...')
        
        # Criar diretório media se não existir
        media_dir = Path(settings.MEDIA_ROOT) if hasattr(settings, 'MEDIA_ROOT') else Path('media')
        if not media_dir.exists():
            media_dir.mkdir(parents=True, exist_ok=True)
            self.stdout.write(self.style.SUCCESS(f'✅ Diretório media criado: {media_dir}'))
        
        # Corrigir permissões
        try:
            os.chmod(media_dir, 0o755)
            self.stdout.write(self.style.SUCCESS('✅ Permissões do diretório media corrigidas'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠️ Não foi possível corrigir permissões: {e}'))
        
        # Verificar configurações de upload
        if hasattr(settings, 'FILE_UPLOAD_PERMISSIONS'):
            self.stdout.write(self.style.SUCCESS('✅ Configurações de upload já definidas'))
        else:
            self.stdout.write(self.style.WARNING('⚠️ Considere definir FILE_UPLOAD_PERMISSIONS nas configurações'))
    
    def fix_paste_issues(self):
        """Corrige problemas de paste"""
        self.stdout.write('📋 Corrigindo problemas de paste...')
        
        # Criar arquivo de inicialização avançado
        init_content = '''/**
 * TinyMCE Advanced Initialization Script
 * Versão otimizada para produção com suporte completo a imagens e vídeos
 */

(function() {
    'use strict';
    
    // Configuração avançada do TinyMCE
    const tinymceAdvancedConfig = {
        selector: 'textarea.tinymce, .tinymce',
        height: 600,
        width: '100%',
        skin: 'oxide',
        content_css: '/static/css/tinymce-content.css',
        
        // Plugins completos
        plugins: [
            'advlist', 'autolink', 'lists', 'link', 'image', 'charmap', 'preview',
            'anchor', 'searchreplace', 'visualblocks', 'code', 'insertdatetime',
            'media', 'table', 'wordcount', 'emoticons', 'nonbreaking', 'directionality',
            'paste', 'textcolor', 'colorpicker', 'textpattern', 'help', 'fullscreen',
            'codesample', 'hr', 'pagebreak', 'quickbars', 'template'
        ].join(' '),
        
        // Toolbar completa
        toolbar: [
            'undo redo | bold italic underline strikethrough | fontselect fontsizeselect formatselect',
            'alignleft aligncenter alignright alignjustify | outdent indent | numlist bullist',
            'forecolor backcolor removeformat | charmap emoticons | subscript superscript',
            'visualblocks visualchars | nonbreaking anchor | link unlink | image media',
            'table tabledelete | tableprops tablerowprops tablecellprops | tableinsertrowbefore tableinsertrowafter tabledeleterow | tableinsertcolbefore tableinsertcolafter tabledeletecol',
            'code codesample | fullscreen preview | help'
        ].join(' | '),
        
        // Menu completo
        menubar: 'file edit view insert format tools table help',
        
        // Configurações de status
        statusbar: true,
        branding: false,
        promotion: false,
        elementpath: true,
        
        // Idioma
        language: 'pt_BR',
        
        // Configurações avançadas de paste
        paste_data_images: true,
        paste_as_text: false,
        paste_auto_cleanup_on_paste: false,
        paste_remove_styles: false,
        paste_remove_styles_if_webkit: false,
        paste_strip_class_attributes: 'none',
        paste_enable_default_filters: false,
        paste_word_valid_elements: '*[*]',
        paste_retain_style_properties: 'color background-color font-size font-family font-weight text-decoration text-align line-height margin padding border',
        paste_merge_formats: true,
        paste_convert_word_fake_lists: false,
        paste_filter_drop: false,
        paste_webkit_styles: 'color background-color font-size font-family',
        paste_preprocess: function(plugin, args) {
            console.log('Paste preprocess - content length:', args.content.length);
            // Permitir imagens e vídeos
            args.content = args.content.replace(/<img[^>]*>/gi, function(match) {
                return match.replace(/on\\w+="[^"]*"/gi, ''); // Remove eventos perigosos
            });
        },
        paste_postprocess: function(plugin, args) {
            console.log('Paste postprocess - content length:', args.content.length);
        },
        
        // Configurações de imagem
        image_advtab: true,
        image_caption: true,
        image_class_list: [
            {title: 'Responsive', value: 'img-fluid'},
            {title: 'Rounded', value: 'rounded'},
            {title: 'Thumbnail', value: 'img-thumbnail'}
        ],
        image_title: true,
        image_dimensions: true,
        image_description: true,
        
        // Configurações de mídia
        media_live_embeds: true,
        media_alt_source: true,
        media_poster: true,
        media_dimensions: true,
        media_url_resolver: 'function(data, resolve, reject) { resolve(data); }',
        media_scripts: [
            {filter: 'iframe', width: 300, height: 150},
            {filter: 'video', width: 300, height: 150}
        ],
        
        // Configurações de validação
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
        
        // Elementos válidos estendidos
        extended_valid_elements: 'span[*],div[*],p[*],br[*],hr[*],h1[*],h2[*],h3[*],h4[*],h5[*],h6[*],ul[*],ol[*],li[*],a[*],img[*],video[*],iframe[*],source[*],track[*],table[*],tr[*],td[*],th[*],thead[*],tbody[*],tfoot[*],caption[*],colgroup[*],col[*],blockquote[*],pre[*],code[*],em[*],strong[*],b[*],i[*],u[*],s[*],del[*],ins[*],mark[*],small[*],sub[*],sup[*],cite[*],q[*],abbr[*],acronym[*],dfn[*],kbd[*],samp[*],var[*],time[*],figure[*],figcaption[*]',
        
        // Elementos inválidos
        invalid_elements: 'script,object,embed,form,input,textarea,select,button,label,fieldset,legend,frame,frameset,noframes,applet,basefont,bgsound,link,meta,style,title,xmp,plaintext,listing,marquee,blink,isindex,dir,menu,center,font,strike,tt,u,big,small,spacer,layers,ilayer,base,basefont,center,font,strike,tt,u,big,small,spacer,layers,ilayer',
        
        // Atributos válidos
        valid_attributes: '*[*]',
        invalid_attributes: 'on*',
        
        // Configurações de interface
        fullscreen_native: true,
        resize: true,
        toolbar_mode: 'sliding',
        toolbar_sticky: true,
        toolbar_sticky_offset: 0,
        
        // URLs
        relative_urls: false,
        remove_script_host: false,
        convert_urls: true,
        
        // Configurações de setup
        setup: function(editor) {
            console.log('TinyMCE editor setup:', editor.id);
            
            // Configurar eventos de paste
            editor.on('PastePreProcess', function(e) {
                console.log('PastePreProcess:', e.content.substring(0, 100));
                // Permitir imagens e vídeos
                e.content = e.content.replace(/<img[^>]*>/gi, function(match) {
                    return match.replace(/on\\w+="[^"]*"/gi, '');
                });
            });
            
            editor.on('PastePostProcess', function(e) {
                console.log('PastePostProcess:', e.node.innerHTML.substring(0, 100));
            });
        },
        
        // Callback de inicialização
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
        
        console.log('Initializing TinyMCE with advanced config...');
        tinymce.init(tinymceAdvancedConfig);
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
        
        # Salvar arquivo
        os.makedirs(settings.STATIC_ROOT / 'js', exist_ok=True)
        with open(settings.STATIC_ROOT / 'js' / 'tinymce-init.js', 'w', encoding='utf-8') as f:
            f.write(init_content)
        
        self.stdout.write(self.style.SUCCESS('✅ Arquivo de inicialização avançado criado'))
    
    def fix_toolbar_issues(self):
        """Corrige problemas da toolbar"""
        self.stdout.write('🔧 Corrigindo problemas da toolbar...')
        
        # Criar CSS avançado
        css_content = '''/* TinyMCE Advanced Content CSS */
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
    margin: 10px 0;
}

img.img-fluid {
    max-width: 100%;
    height: auto;
}

img.rounded {
    border-radius: 8px;
}

img.img-thumbnail {
    padding: 4px;
    border: 1px solid #ddd;
    border-radius: 4px;
    max-width: 100%;
    height: auto;
}

video {
    max-width: 100%;
    height: auto;
    border-radius: 4px;
    margin: 10px 0;
}

iframe {
    max-width: 100%;
    border-radius: 4px;
    margin: 10px 0;
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

figure {
    margin: 1em 0;
    text-align: center;
}

figcaption {
    font-size: 0.9em;
    color: #666;
    margin-top: 0.5em;
    font-style: italic;
}

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
    
    img, video, iframe {
        margin: 5px 0;
    }
}

.tox-tinymce {
    border-radius: 0.375rem;
    border: 1px solid #ced4da;
}

.tox-toolbar__primary {
    background: #f8f9fa !important;
    border-bottom: 1px solid #dee2e6;
}

.tox-editor-header {
    border-bottom: 1px solid #dee2e6;
}

.tox-statusbar {
    border-top: 1px solid #dee2e6;
    background: #f8f9fa !important;
}

.tox-edit-area {
    background: #fff;
}

.tox-edit-area iframe {
    background: #fff;
}
'''
        
        # Salvar CSS
        os.makedirs(settings.STATIC_ROOT / 'css', exist_ok=True)
        with open(settings.STATIC_ROOT / 'css' / 'tinymce-content.css', 'w', encoding='utf-8') as f:
            f.write(css_content)
        
        self.stdout.write(self.style.SUCCESS('✅ CSS avançado criado'))
    
    def update_settings(self):
        """Atualiza configurações do Django"""
        self.stdout.write('⚙️ Atualizando configurações...')
        
        # Verificar se as configurações estão corretas
        if hasattr(settings, 'TINYMCE_DEFAULT_CONFIG'):
            self.stdout.write(self.style.SUCCESS('✅ Configurações do TinyMCE já definidas'))
        else:
            self.stdout.write(self.style.WARNING('⚠️ Considere definir TINYMCE_DEFAULT_CONFIG nas configurações'))
        
        # Verificar configurações de mídia
        if hasattr(settings, 'MEDIA_URL') and hasattr(settings, 'MEDIA_ROOT'):
            self.stdout.write(self.style.SUCCESS('✅ Configurações de mídia definidas'))
        else:
            self.stdout.write(self.style.WARNING('⚠️ Considere definir MEDIA_URL e MEDIA_ROOT nas configurações'))
    
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
    
    def test_features(self):
        """Testa funcionalidades"""
        self.stdout.write('🧪 Testando funcionalidades...')
        
        try:
            # Verificar se os arquivos existem
            files_to_check = [
                settings.STATIC_ROOT / 'js' / 'tinymce-init.js',
                settings.STATIC_ROOT / 'css' / 'tinymce-content.css',
            ]
            
            for file_path in files_to_check:
                if file_path.exists():
                    self.stdout.write(f'✅ {file_path}')
                else:
                    self.stdout.write(self.style.ERROR(f'❌ {file_path} não encontrado'))
                    return False
            
            # Verificar diretório media
            media_dir = Path(settings.MEDIA_ROOT) if hasattr(settings, 'MEDIA_ROOT') else Path('media')
            if media_dir.exists():
                self.stdout.write(f'✅ {media_dir}')
            else:
                self.stdout.write(self.style.WARNING(f'⚠️ {media_dir} não encontrado'))
            
            self.stdout.write(self.style.SUCCESS('✅ Todas as funcionalidades estão configuradas'))
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro no teste: {e}'))
            return False 