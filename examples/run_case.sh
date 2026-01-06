#!/usr/bin/env bash
set -euo pipefail

SERIAL=${1:-"demo-serial"}
RULES_DIR=${2:-"samples/rules"}
CASE_DIR=${3:-".case"}

# 可选：提供 config.json 覆盖参数
CONFIG=${CONFIG:-""}

cmd=(mybugreport-pipeline tool run adb --serial "$SERIAL" --rules "$RULES_DIR" --out "$CASE_DIR")
if [ -n "$CONFIG" ]; then
  cmd+=(--config "$CONFIG")
fi

"${cmd[@]}"

echo "Case stored under $CASE_DIR"
