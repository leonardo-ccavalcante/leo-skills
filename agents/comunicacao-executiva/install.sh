#!/usr/bin/env bash
# Instalador do sistema de agentes "Comunicação Executiva".
# Copia os 13 agentes + a base de evidência (N1) para ~/.claude/agents/.
# NÃO copia ce-memoria/ (N2 = dado pessoal). Ver README.md.

set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/agents"
DEST="${CLAUDE_AGENTS_DIR:-$HOME/.claude/agents}"

if [[ ! -d "$SRC" ]]; then
  echo "erro: pasta 'agents/' não encontrada em $SRC" >&2
  exit 1
fi

echo "Instalando de: $SRC"
echo "Instalando em: $DEST"
echo

mkdir -p "$DEST/ce-base"

# 1. Os 13 agentes (.md na raiz de agents/)
count=0
for f in "$SRC"/*.md; do
  [[ -e "$f" ]] || continue
  cp "$f" "$DEST/"
  echo "  agente  $(basename "$f")"
  count=$((count + 1))
done

# 2. Base de evidência N1 (imutável)
for f in "$SRC"/ce-base/*.md; do
  [[ -e "$f" ]] || continue
  cp "$f" "$DEST/ce-base/"
  echo "  base    ce-base/$(basename "$f")"
done

# 3. Esqueleto da memória N2 — criado vazio, NUNCA sobrescrito
if [[ -d "$DEST/ce-memoria" ]]; then
  echo
  echo "  memória ce-memoria/ já existe — preservada intacta."
else
  mkdir -p "$DEST/ce-memoria/audiencias"
  cp "$SRC/ce-memoria/README.md" "$DEST/ce-memoria/"
  echo
  echo "  memória ce-memoria/ criada vazia (aprendizado começa do zero)."
  echo "          Para levar aprendizado de outra máquina, copie a pasta ce-memoria/ manualmente."
fi

echo
echo "Pronto. $count agentes instalados."
echo
echo "Para usar, peça na conversa:"
echo "  \"use o agente comunicacao-executiva\""
echo
echo "Verificação de portabilidade (deve não retornar nada):"
echo "  grep -rl 'PC_Brain\|Papers & Ensaios' \"$DEST\""
