#!/bin/bash
# Uso: bash scripts/find_orphan_template_references.sh orfaos.txt

if [ -z "$1" ]; then
  echo "Uso: $0 <arquivo_com_lista_de_templates>"
  exit 1
fi

LISTA="$1"

while IFS= read -r template; do
  if [ -n "$template" ]; then
    echo "\nBuscando referências para: $template"
    grep -rnw . -e "$template" || echo "Nenhuma referência encontrada."
  fi
done < "$LISTA" 