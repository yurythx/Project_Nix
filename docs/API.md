# Documentação da API REST

Bem-vindo à documentação da API REST do Project Nix. Esta documentação fornece informações detalhadas sobre como interagir com nossa API, incluindo autenticação, endpoints disponíveis, códigos de status e exemplos de requisições e respostas.

## 📋 Índice

- [🔑 Autenticação](#-autenticação)
- [📡 Endpoints](#-endpoints)
  - [Artigos](#artigos)
  - [Contas de Usuário](#contas-de-usuário)
  - [Livros](#livros)
  - [Mangás](#mangás)
  - [Audiobooks](#audiobooks)
- [📦 Formato das Respostas](#-formato-das-respostas)
- [🔒 Segurança](#-segurança)
- [⚡ Limites de Taxa](#-limites-de-taxa)
- [🔍 Filtros e Busca](#-filtros-e-busca)
- [📚 Documentação Interativa](#-documentação-interativa)

## 🔑 Autenticação

A API do Project Nix usa autenticação baseada em token. Para autenticar suas requisições, você precisará incluir um token de acesso no cabeçalho `Authorization`.

### Obtendo um Token

```http
POST /api/auth/token/
Content-Type: application/json

{
    "username": "seu_usuario",
    "password": "sua_senha"
}
```

**Resposta de Sucesso (200 OK):**
```json
{
    "token": "seu_token_aqui",
    "user": {
        "id": 1,
        "username": "seu_usuario",
        "email": "usuario@exemplo.com"
    }
}
```

### Usando o Token

Inclua o token no cabeçalho `Authorization` de todas as requisições autenticadas:

```
Authorization: Token seu_token_aqui
```

## 📡 Endpoints

### Artigos

#### Listar Artigos
```http
GET /api/articles/
```

**Parâmetros de Consulta:**
- `category` - Filtrar por categoria (ID ou slug)
- `tag` - Filtrar por tag (nome)
- `author` - Filtrar por autor (ID de usuário)
- `search` - Busca por termo no título ou conteúdo
- `status` - Filtrar por status (publicado, rascunho, arquivado)
- `ordering` - Ordenação (ex: `-created_at` para mais recentes primeiro)
- `page` - Número da página (paginação)

**Exemplo de Resposta (200 OK):**
```json
{
    "count": 42,
    "next": "https://api.projectnix.com/api/articles/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "title": "Título do Artigo",
            "slug": "titulo-do-artigo",
            "excerpt": "Resumo do artigo...",
            "content": "Conteúdo completo do artigo...",
            "status": "published",
            "created_at": "2023-01-01T12:00:00Z",
            "updated_at": "2023-01-01T12:00:00Z",
            "published_at": "2023-01-01T12:00:00Z",
            "author": {
                "id": 1,
                "username": "autor",
                "first_name": "Nome",
                "last_name": "Sobrenome"
            },
            "categories": [
                {"id": 1, "name": "Tecnologia", "slug": "tecnologia"}
            ],
            "tags": [
                {"id": 1, "name": "python", "slug": "python"}
            ]
        }
    ]
}
```

#### Obter Detalhes de um Artigo
```http
GET /api/articles/{id}/
```

#### Criar um Novo Artigo (Autenticação necessária)
```http
POST /api/articles/
Authorization: Token seu_token_aqui
Content-Type: application/json

{
    "title": "Novo Artigo",
    "content": "Conteúdo do artigo...",
    "excerpt": "Resumo do artigo...",
    "status": "draft",
    "categories": [1, 2],
    "tags": ["python", "django"]
}
```

### Contas de Usuário

#### Registrar Novo Usuário
```http
POST /api/auth/register/
Content-Type: application/json

{
    "username": "novousuario",
    "email": "usuario@exemplo.com",
    "password": "senhasegura123",
    "password_confirm": "senhasegura123"
}
```

#### Obter Perfil do Usuário (Autenticação necessária)
```http
GET /api/auth/me/
Authorization: Token seu_token_aqui
```

### Livros

#### Listar Livros
```http
GET /api/books/
```

**Parâmetros de Consulta:**
- `author` - Filtrar por autor
- `genre` - Filtrar por gênero
- `published_after` - Filtrar por data de publicação (YYYY-MM-DD)
- `search` - Busca por título, autor ou descrição
- `ordering` - Ordenação (ex: `-published_date`)

### Mangás

#### Listar Mangás
```http
GET /api/mangas/
```

**Parâmetros de Consulta:**
- `status` - Filtrar por status (em_andamento, finalizado, hiato)
- `demographic` - Filtrar por demografia (shonen, shojo, seinen, josei)
- `genre` - Filtrar por gênero
- `author` - Filtrar por autor
- `search` - Busca por título, autor ou descrição

### Audiobooks

#### Listar Audiobooks
```http
GET /api/audiobooks/
```

**Parâmetros de Consulta:**
- `author` - Filtrar por autor
- `narrator` - Filtrar por narrador
- `duration_min` - Duração mínima em minutos
- `duration_max` - Duração máxima em minutos
- `search` - Busca por título, autor ou descrição

## 📦 Formato das Respostas

Todas as respostas da API seguem um formato consistente:

### Sucesso (200 OK)
```json
{
    "status": "success",
    "data": {
        // Dados da resposta
    },
    "meta": {
        // Metadados adicionais (opcional)
    }
}
```

### Erro (4xx/5xx)
```json
{
    "status": "error",
    "error": {
        "code": "error_code",
        "message": "Mensagem de erro descritiva",
        "details": {
            // Detalhes adicionais do erro (opcional)
        }
    }
}
```

### Códigos de Status HTTP

| Código | Descrição |
|--------|------------|
| 200 | OK - Requisição bem-sucedida |
| 201 | Criado - Recurso criado com sucesso |
| 204 | Sem Conteúdo - Exclusão bem-sucedida |
| 400 | Requisição Inválida - Erro de validação ou dados ausentes |
| 401 | Não Autorizado - Autenticação necessária |
| 403 | Proibido - Permissões insuficientes |
| 404 | Não Encontrado - Recurso não existe |
| 405 | Método Não Permitido - Método HTTP não suportado |
| 429 | Muitas Requisições - Limite de taxa excedido |
| 500 | Erro Interno do Servidor - Erro inesperado |

## 🔒 Segurança

### Autenticação
- Todas as requisições devem usar HTTPS
- Tokens de acesso devem ser mantidos em segredo e nunca compartilhados
- Tokens expiram após 24 horas por padrão (configurável)

### Permissões
- Acesso de leitura (GET) é público para a maioria dos recursos
- Operações de escrita (POST, PUT, PATCH, DELETE) requerem autenticação
- Permissões específicas podem ser necessárias dependendo do recurso

### CORS
- A API suporta CORS (Cross-Origin Resource Sharing)
- Apenas origens confiáveis são permitidas por padrão
- Solicitações de origens não autorizadas serão rejeitadas

## ⚡ Limites de Taxa

A API implementa limites de taxa para evitar abuso:

- **Anônimos**: 100 requisições por dia
- **Usuários autenticados**: 1.000 requisições por dia
- **Endpoints específicos** podem ter limites adicionais

Cabeçalhos de resposta incluem informações sobre os limites de taxa:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 998
X-RateLimit-Reset: 1625097600
```

## 🔍 Filtros e Busca

A maioria dos endpoints de lista suporta filtragem avançada:

### Filtros Básicos
```
GET /api/books/?author=2&status=published
```

### Busca por Texto
```
GET /api/books/?search=django
```

### Filtros de Intervalo
```
GET /api/books/?published_after=2023-01-01&published_before=2023-12-31
```

### Ordenação
```
GET /api/books/?ordering=-published_date,title
```

### Paginação
```
GET /api/books/?page=2&page_size=20
```

## 📚 Documentação Interativa

Para uma experiência interativa com a API, acesse:

- **Swagger UI**: `/api/docs/`
- **ReDoc**: `/api/redoc/`

Estas interfaces permitem:
- Visualizar todos os endpoints disponíveis
- Fazer requisições de teste diretamente do navegador
- Ver exemplos de requisições e respostas
- Autenticar-se diretamente na interface

## 📞 Suporte

Em caso de dúvidas ou problemas com a API, entre em contato:

- E-mail: suporte@projectnix.com
- Issues: [GitHub Issues](https://github.com/seu-usuario/project-nix/issues)
- Discord: [Servidor de Suporte](https://discord.gg/)

---

📅 Última atualização: Julho 2023  
🔒 Versão da API: v1
