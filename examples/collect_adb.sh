#!/usr/bin/env bash
set -euo pipefail

# 示例：使用 mybugreport-pipeline 采集设备日志。
# 使用前请在有 adb 的环境下，并确认设备序列号。

SERIAL=${1:-"demo-serial"}
OUT_DIR=${2:-".work/adb"}

mybugreport-pipeline tool collect adb \
  --serial "$SERIAL" \
  --out "$OUT_DIR" \
  --buffers main,system \
  --dmesg \
  --bugreport

echo "Artifacts stored under $OUT_DIR"
