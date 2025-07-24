# Guia de Contribuição

Obrigado por considerar contribuir para o Project Nix! Este guia irá ajudá-lo a configurar o ambiente de desenvolvimento, entender a estrutura do projeto e enviar suas contribuições.

## 📋 Índice

- [📝 Código de Conduta](#-código-de-conduta)
- [🛠️ Configuração do Ambiente](#️-configuração-do-ambiente)
- [🔧 Fluxo de Trabalho](#-fluxo-de-trabalho)
- [📝 Convenções de Código](#-convenções-de-código)
- [🧪 Testes](#-testes)
- [📚 Documentação](#-documentação)
- [🔍 Revisão de Código](#-revisão-de-código)
- [📦 Envio de Pull Requests](#-envio-de-pull-requests)
- [🏷️ Versionamento](#️-versionamento)
- [🤝 Suporte](#-suporte)

## 📝 Código de Conduta

Antes de começar, por favor leia nosso [Código de Conduta](docs/CODE_OF_CONDUCT.md). Esperamos que todos os colaboradores sigam estas diretrizes para mantermos uma comunidade acolhedora e respeitosa.

## 🛠️ Configuração do Ambiente

### Pré-requisitos

- Python 3.11+
- PostgreSQL 12+
- Git
- Node.js 16+ (para assets frontend)

### Configuração Inicial

1. **Fork o repositório**
   ```bash
   # No GitHub, clique em "Fork"
   # Clone seu fork localmente
   git clone https://github.com/seu-usuario/project-nix.git
   cd project-nix
   ```

2. **Configure o ambiente virtual**
   ```bash
   python -m venv venv
   # No Linux/macOS
   source venv/bin/activate
   # No Windows
   .\venv\Scripts\activate
   ```

3. **Instale as dependências**
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Configure as variáveis de ambiente**
   ```bash
   cp .env.example .env
   # Edite o .env com suas configurações locais
   ```

5. **Configure o banco de dados**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py loaddata initial_data
   ```

6. **Inicie o servidor de desenvolvimento**
   ```bash
   python manage.py runserver
   ```

## 🔧 Fluxo de Trabalho

1. **Crie uma branch para sua feature/fix**
   ```bash
   git checkout -b feature/nome-da-feature
   # ou
   git checkout -b fix/nome-do-bug
   ```

2. **Faça commit das suas mudanças**
   ```bash
   git add .
   git commit -m "Descrição clara e concisa das mudanças"
   ```

3. **Envie as alterações**
   ```bash
   git push origin sua-branch
   ```

4. **Abra um Pull Request**
   - Vá para o repositório no GitHub
   - Clique em "New Pull Request"
   - Preencha o template do PR
   - Adicione revisores se necessário

## 📝 Convenções de Código

### Python
- Siga o [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use docstrings no formato Google
- Nomes de classes em `CamelCase`
- Nomes de funções e variáveis em `snake_case`
- Constantes em `UPPER_CASE`

### HTML/CSS/JavaScript
- Siga as [Diretrizes de HTML5](https://developer.mozilla.org/pt-BR/docs/Web/Guide/HTML/HTML5)
- Use CSS com metodologia BEM
- Siga o [Guia de Estilo JavaScript](https://github.com/airbnb/javascript)

### Commits
- Use o [Conventional Commits](https://www.conventionalcommits.org/)
- Exemplos:
  ```
  feat: adiciona autenticação via Google
  fix: corrige erro de validação no formulário
  docs: atualiza documentação da API
  style: formata código de acordo com o linter
  refactor: melhora estrutura do serviço de usuários
  test: adiciona testes para o módulo de artigos
  chore: atualiza dependências
  ```

## 🧪 Testes

### Executando Testes
```bash
# Todos os testes
pytest

# Testes específicos
pytest apps/accounts/tests/test_views.py

# Com cobertura
coverage run -m pytest
coverage report -m
```

### Escrevendo Testes
- Testes unitários devem estar no diretório `tests/unit`
- Testes de integração em `tests/integration`
- Use fixtures para dados de teste comuns
- Nomeie os arquivos de teste como `test_*.py`

## 📚 Documentação

### Documentação do Código
- Use docstrings detalhadas
- Documente todas as funções públicas
- Inclua exemplos de uso quando relevante

### Documentação do Projeto
- Atualize o README.md para mudanças significativas
- Adicione documentação em `/docs` quando necessário
- Atualize os comentários do código quando fizer alterações

### Criando Documentação Nova
1. Crie um novo arquivo Markdown em `/docs`
2. Adicione um link no `docs/README.md`
3. Siga o estilo consistente com o resto da documentação

## 🔍 Revisão de Código

### Diretrizes para Revisores
- Seja respeitoso e construtivo
- Foque no código, não no autor
- Explique o porquê das sugestões
- Aprecie boas práticas

### Respondendo a Comentários
- Responda a todos os comentários
- Faça as alterações solicitadas ou explique por que não as fez
- Marque os comentários como resolvidos quando tratados

## 📦 Envio de Pull Requests

1. **Verifique se seu código está pronto**
   - [ ] Todos os testes passam
   - [ ] O código segue as diretrizes de estilo
   - [ ] A documentação foi atualizada
   - [ ] Os commits seguem o Conventional Commits

2. **Crie um Pull Request**
   - Preencha o template do PR
   - Descreva as mudanças e o motivo
   - Inclua capturas de tela quando apropriado
   - Adicione revisores

3. **Enderece os comentários**
   - Faça as alterações necessárias
   - Adicione commits adicionais se necessário
   - Rebase seu branch se solicitado

## 🏷️ Versionamento

Usamos [Semantic Versioning](https://semver.org/) para versionamento. Dado um número de versão MAJOR.MINOR.PATCH:

- **MAJOR**: Mudanças incompatíveis na API
- **MINOR**: Adição de funcionalidades compatíveis
- **PATCH**: Correções de bugs compatíveis

## 🤝 Suporte

Se precisar de ajuda:
1. Consulte a [documentação](docs/README.md)
2. Procure por issues relacionadas
3. Se não encontrar, abra uma nova issue

Para discussões gerais, junte-se ao nosso [Discord](https://discord.gg/)

---

Obrigado por contribuir para o Project Nix! Sua ajuda é muito valiosa para nós. 💜
