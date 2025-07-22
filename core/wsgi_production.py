"""
WSGI config for FireFlies CMS production.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import sys
from pathlib import Path

# Adicionar o diretório do projeto ao path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Configurar variáveis de ambiente para produção
os.environ.setdefault('ENVIRONMENT', 'production')
os.environ.setdefault('DEBUG', 'False')

# Importar configurações de produção
from django.core.wsgi import get_wsgi_application

# Configurar o Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Aplicar configurações de produção
try:
    from core.production import *
    print("✅ Configurações de produção carregadas")
except ImportError:
    print("⚠️ Arquivo de configuração de produção não encontrado, usando configurações padrão")

# Obter a aplicação WSGI
application = get_wsgi_application()

# Configurações adicionais para produção
if os.environ.get('ENVIRONMENT') == 'production':
    # Configurar logging para produção
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(BASE_DIR / 'logs' / 'wsgi.log'),
            logging.StreamHandler()
        ]
    )
    
    print("🚀 Servidor WSGI de produção iniciado")
    print(f"📁 Diretório base: {BASE_DIR}")
    print(f"🌍 Ambiente: {os.environ.get('ENVIRONMENT', 'production')}")
    print(f"🐛 Debug: {os.environ.get('DEBUG', 'False')}") 