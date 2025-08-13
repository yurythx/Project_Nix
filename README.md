# Project Nix

Sistema de gerenciamento de conteúdo modular baseado em Django.

## 📦 Requisitos

- Python 3.8+
- PostgreSQL/MySQL (produção) ou SQLite (desenvolvimento)
- Redis (opcional, para cache e Celery)
- Node.js e NPM (para assets estáticos)

## 🚀 Iniciando o Desenvolvimento

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/project-nix.git
   cd project-nix
   ```

2. Crie e ative o ambiente virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate    # Windows
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure as variáveis de ambiente:
   ```bash
   cp .env.example .env
   # Edite o arquivo .env com suas configurações
   ```

5. Execute as migrações:
   ```bash
   python manage.py migrate
   ```

6. Crie um superusuário:
   ```bash
   python manage.py createsuperuser
   ```

7. Inicie o servidor de desenvolvimento:
   ```bash
   python manage.py runserver
   ```

## 🚀 Deploy no aapanel

Para instruções detalhadas de implantação no painel aapanel, consulte o [Guia de Deploy no aapanel](docs/DEPLOY_AAPANEL.md).

## 🛠️ Comandos Úteis

- Iniciar servidor de desenvolvimento: `python manage.py runserver`
- Criar migrações: `python manage.py makemigrations`
- Aplicar migrações: `python manage.py migrate`
- Coletar arquivos estáticos: `python manage.py collectstatic`
- Iniciar Celery worker: `celery -A core worker -l info`
- Iniciar Celery beat: `celery -A core beat -l info`

## 📚 Documentação

- [Guia de Deploy no aapanel](docs/DEPLOY_AAPANEL.md)
- [Documentação do Django](https://docs.djangoproject.com/)
- [Documentação do Celery](https://docs.celeryq.dev/)

## 📄 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.
