#!/usr/bin/env bash
set -euo pipefail
echo "== EOQ Pro: Packaging demo (macOS/Linux) =="
ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$ROOT"

APP_NAME="EOQ_Pro"
BIN_NAME="EOQ_Pro"
OUT_DIR="EOQ_Pro_Demo"
ZIP_MAC="eoq_pro_macos.zip"
ZIP_LIN="eoq_pro_linux.zip"

rm -rf build dist "$OUT_DIR" "$ZIP_MAC" "$ZIP_LIN" || true

if [[ "${SKIP_BUILD:-}" != "1" ]]; then
  ICONOPT=""; [[ -f app.icns ]] && ICONOPT="--icon app.icns"
  VEROPT="";  [[ -f version_info.txt ]] && VEROPT="--version-file version_info.txt"
  KEYOPT="";  [[ -n "${PYI_KEY:-}" ]] && KEYOPT="--key ${PYI_KEY}"
  echo "Compilo con PyInstaller..."
  python3 -m PyInstaller --noconsole --onefile --name "${BIN_NAME}" $ICONOPT $VEROPT $KEYOPT eoq_pro.py
fi

mkdir -p "$OUT_DIR"

if [[ -f "dist/${BIN_NAME}" ]]; then cp "dist/${BIN_NAME}" "$OUT_DIR/"; fi
if [[ -d "dist/${BIN_NAME}.app" ]]; then cp -R "dist/${BIN_NAME}.app" "$OUT_DIR/"; fi
[[ -f Guida_EOQ_Pro_Semplice_compact.pdf ]] && cp Guida_EOQ_Pro_Semplice_compact.pdf "$OUT_DIR/Guida_EOQ_Pro.pdf"
[[ -f Guida_EOQ_Pro_Semplice.txt ]] && cp Guida_EOQ_Pro_Semplice.txt "$OUT_DIR/Guida_EOQ_Pro.txt"
[[ -f README_EOQ_Pro_Semplice.md ]] && cp README_EOQ_Pro_Semplice.md "$OUT_DIR/README.md"
[[ -f EULA.txt ]] && cp EULA.txt "$OUT_DIR/"
[[ -f Privacy_Policy.txt ]] && cp Privacy_Policy.txt "$OUT_DIR/"
[[ -f eoq_demo_sample.csv ]] && cp eoq_demo_sample.csv "$OUT_DIR/"
[[ -f brand_logo.svg ]] && cp brand_logo.svg "$OUT_DIR/"
[[ -f VERSION ]] && cp VERSION "$OUT_DIR/"

if [[ "$OSTYPE" == "darwin"* ]]; then
  ditto -c -k --sequesterRsrc --keepParent "$OUT_DIR" "$ZIP_MAC"
  unzip -l "$ZIP_MAC" | awk '{print tolower($0)}' | grep -E "\.py$" && { echo "ERRORE: trovati .py nello zip"; exit 1; } || echo "Verifica OK: nessun .py nello ZIP."
  echo "Creato: $ZIP_MAC"
else
  zip -r "$ZIP_LIN" "$OUT_DIR" >/dev/null
  unzip -l "$ZIP_LIN" | awk '{print tolower($0)}' | grep -E "\.py$" && { echo "ERRORE: trovati .py nello zip"; exit 1; } || echo "Verifica OK: nessun .py nello ZIP."
  echo "Creato: $ZIP_LIN"
fi
