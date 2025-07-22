# Accounts

## Responsabilidade
Gerencia autenticação, perfis de usuário, registro, login, recuperação de senha e configurações de conta.

## Estrutura
- `models/`: Modelos de usuário e verificação.
- `views/`: Views para login, registro, perfil, etc.
- `forms/`: Formulários de autenticação, registro, perfil.
- `services/`: Lógica de autenticação, email, perfil.
- `repositories/`: Acesso a dados de usuário e verificação.
- `templates/`: Templates HTML de contas.
- `management/commands/`: Comandos customizados (ex: criar superusuário).

## Integração
- Usa signals para ações pós-registro e pós-login.
- Integra com app `config` para permissões/admin.

## Pontos de atenção
- Regras de negócio de autenticação e segurança.
- Validação de email e senha forte. 