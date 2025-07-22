#!/bin/bash

# Limpa o arquivo .env, removendo qualquer linha que não esteja no formato VARIAVEL=valor
# Mantém apenas linhas válidas para variáveis de ambiente

ENV_FILE=".env"
BACKUP_FILE=".env.bak"

if [[ ! -f "$ENV_FILE" ]]; then
    echo "Arquivo $ENV_FILE não encontrado."
    exit 0
fi

cp "$ENV_FILE" "$BACKUP_FILE"

# Mantém apenas linhas que começam com letras maiúsculas, números ou _, seguidas de =
grep -E '^[A-Z0-9_]+=' "$BACKUP_FILE" > "$ENV_FILE"

echo "Arquivo $ENV_FILE limpo! (backup salvo em $BACKUP_FILE)" 