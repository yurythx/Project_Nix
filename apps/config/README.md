# Config

## Responsabilidade
Gerencia configurações do sistema, módulos, permissões, email e banco de dados.

## Estrutura
- `models/`: Modelos de configuração, módulos, logs.
- `views/`: Views para dashboard, email, módulos, usuários.
- `forms/`: Formulários de configuração e email.
- `services/`: Lógica de configuração, email, módulos.
- `repositories/`: Acesso a dados de configuração e permissões.
- `templates/`: Templates HTML do painel admin/config.
- `management/commands/`: Comandos customizados para setup e diagnóstico.

## Integração
- Integra com todas as apps para centralizar permissões e módulos.
- Usa signals para logs e auditoria.

## Pontos de atenção
- Segurança de permissões.
- Consistência de configurações entre ambientes. 