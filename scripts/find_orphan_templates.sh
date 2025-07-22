#!/bin/bash
# Lista templates HTML não referenciados em views, urls ou outros templates

TEMPLATES_DIR=apps
CODE_DIR=apps

find $TEMPLATES_DIR -type f -name '*.html' | while read file; do
    fname=$(basename "$file")
    # Procura referência no código e templates
    grep -q "$fname" $CODE_DIR || echo "Órfão: $file"
done 