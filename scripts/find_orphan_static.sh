#!/bin/bash
# Lista arquivos estáticos não referenciados em templates ou código Python

STATIC_DIR=static
TEMPLATES_DIR=apps
CODE_DIR=apps

find $STATIC_DIR -type f \( -name '*.css' -o -name '*.js' -o -name '*.png' -o -name '*.jpg' -o -name '*.svg' \) | while read file; do
    fname=$(basename "$file")
    # Procura referência no código e templates
    grep -q "$fname" $TEMPLATES_DIR $CODE_DIR || echo "Órfão: $file"
done 