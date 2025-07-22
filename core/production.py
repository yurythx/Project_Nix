"""
Configurações específicas para produção
Este arquivo deve ser importado no settings.py principal ou usado diretamente
"""

import os
from pathlib import Path

# Configurações de produção
DEBUG = False
ENVIRONMENT = 'production'

# Configurações de segurança para produção
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 ano
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Cookies seguros
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Configurações de mídia e estáticos para produção
BASE_DIR = Path(__file__).resolve().parent.parent

# Configurações de mídia
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Configurações de estáticos
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Configurações de storage para produção
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Configurações de cache para produção
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Configurações de logging para produção
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Configurações de CSRF para produção
CSRF_TRUSTED_ORIGINS = [
    'https://yourdomain.com',
    'https://www.yourdomain.com',
]

# Configurações de sessão para produção
SESSION_COOKIE_AGE = 86400  # 24 horas
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = False

# Configurações de rate limiting para produção
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'

# Configurações de email para produção (se necessário)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

# Configurações de banco de dados para produção (se necessário)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Configurações de TinyMCE otimizadas para produção
TINYMCE_DEFAULT_CONFIG = {
    'height': 500,
    'width': '100%',
    'cleanup_on_startup': True,
    'custom_undo_redo_levels': 20,
    'theme': 'silver',
    'plugins': '''
        advlist autolink lists link image charmap preview anchor
        searchreplace visualblocks code insertdatetime media
        table wordcount emoticons nonbreaking directionality
    ''',
    'toolbar1': '''
        undo redo | bold italic underline strikethrough | fontselect fontsizeselect formatselect |
        alignleft aligncenter alignright alignjustify | outdent indent | numlist bullist |
        forecolor backcolor removeformat | charmap emoticons
    ''',
    'toolbar2': '''
        visualblocks visualchars | nonbreaking anchor | link unlink | image media |
        table | code | customfullscreen | preview | help
    ''',
    'menubar': True,
    'statusbar': True,
    'branding': False,
    'promotion': False,
    'contextmenu': 'link image table',
    'directionality': 'ltr',
    'language': 'pt_BR',
    'paste_data_images': True,
    'paste_as_text': False,
    'paste_auto_cleanup_on_paste': True,
    'paste_remove_styles': False,
    'paste_remove_styles_if_webkit': False,
    'paste_strip_class_attributes': 'none',
    'fullscreen_native': True,
    'resize': False,
    'elementpath': False,
    'toolbar_mode': 'sliding',
    'toolbar_sticky': True,
    # Configurações específicas para produção
    'relative_urls': False,
    'remove_script_host': False,
    'convert_urls': True,
    'verify_html': False,
    'cleanup': True,
    'cleanup_on_startup': True,
    'forced_root_block': 'p',
    'force_br_newlines': False,
    'force_p_newlines': True,
    'remove_linebreaks': False,
    'convert_newlines_to_brs': False,
    'remove_redundant_brs': True,
    'remove_trailing_brs': True,
    'entity_encoding': 'raw',
    'encoding': 'xml',
    'element_format': 'html',
    'schema': 'html5',
    'valid_children': '+body[style]',
    'extended_valid_elements': 'span[*],div[*],p[*],br[*],hr[*],h1[*],h2[*],h3[*],h4[*],h5[*],h6[*],ul[*],ol[*],li[*],a[*],img[*],table[*],tr[*],td[*],th[*],thead[*],tbody[*],tfoot[*],caption[*],colgroup[*],col[*],blockquote[*],pre[*],code[*],em[*],strong[*],b[*],i[*],u[*],s[*],del[*],ins[*],mark[*],small[*],sub[*],sup[*],cite[*],q[*],abbr[*],acronym[*],dfn[*],kbd[*],samp[*],var[*],time[*]',
    'invalid_elements': 'script,object,embed,form,input,textarea,select,button,label,fieldset,legend,iframe,frame,frameset,noframes,applet,basefont,bgsound,link,meta,style,title,xmp,plaintext,listing,marquee,blink,isindex,dir,menu,center,font,strike,tt,u,big,small,spacer,layers,ilayer,base,basefont,center,font,strike,tt,u,big,small,spacer,layers,ilayer',
    'valid_attributes': '*[*]',
    'invalid_attributes': 'on*',
}

# Configurações de Crispy Forms para produção
CRISPY_FAIL_SILENTLY = True

# Configurações de health check para produção
HEALTH_CHECK_ENABLED = True

# Configurações de monitoramento para produção
SENTRY_DSN = os.environ.get('SENTRY_DSN', '')

# Configurações de backup para produção
BACKUP_DIR = os.environ.get('BACKUP_DIR', 'backups')
BACKUP_RETENTION_DAYS = int(os.environ.get('BACKUP_RETENTION_DAYS', '30'))

# Configurações de site para produção
SITE_URL = os.environ.get('SITE_URL', 'https://yourdomain.com')

# Configurações de módulos ativos para produção
ACTIVE_MODULES = os.environ.get('ACTIVE_MODULES', 'accounts,config,pages,articles').split(',')

# Configurações de tema e localização para produção
DEFAULT_THEME = os.environ.get('DEFAULT_THEME', 'light')
DEFAULT_LANGUAGE = os.environ.get('DEFAULT_LANGUAGE', 'pt-br')
DEFAULT_TIMEZONE = os.environ.get('DEFAULT_TIMEZONE', 'America/Sao_Paulo') 