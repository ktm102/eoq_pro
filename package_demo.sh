#!/usr/bin/env bash
set -euo pipefail
APP_NAME_DIR="EOQ_Pro_Demo"
OUT_BASENAME="eoq_pro_demo"
BIN_NAME="EOQ_Pro"

VERSION="${VERSION:-$( [ -f VERSION ] && head -n1 VERSION || echo 1.0.0 )}"
OUT_ZIP="${OUT_BASENAME}_v${VERSION}.zip"
echo "== EOQ Pro: Packaging demo (Linux/macOS) =="
echo "Versione: $VERSION"

if command -v pyinstaller >/dev/null 2>&1 && [[ "${SKIP_BUILD:-0}" != "1" ]]; then
  ADDDATA=""
  [[ -f brand_logo.svg ]] && ADDDATA="--add-data brand_logo.svg:."
  pyinstaller --noconsole --onefile --name "$BIN_NAME" $ADDDATA eoq_pro.py || echo "Build fallita, continuo senza eseguibile."
else
  echo "PyInstaller non trovato o build saltata."
fi

rm -rf "$APP_NAME_DIR"; mkdir -p "$APP_NAME_DIR"
cp eoq_pro.py "$APP_NAME_DIR/"
[[ -f Guida_EOQ_Pro_Semplice.txt ]] && cp Guida_EOQ_Pro_Semplice.txt "$APP_NAME_DIR/Guida_EOQ_Pro.txt"
[[ -f README_EOQ_Pro_Semplice.md ]] && cp README_EOQ_Pro_Semplice.md "$APP_NAME_DIR/README.md"
[[ -f EULA.txt ]] && cp EULA.txt "$APP_NAME_DIR/"
[[ -f Privacy_Policy.txt ]] && cp Privacy_Policy.txt "$APP_NAME_DIR/"
[[ -f eoq_demo_sample.csv ]] && cp eoq_demo_sample.csv "$APP_NAME_DIR/"
[[ -f brand_logo.svg ]] && cp brand_logo.svg "$APP_NAME_DIR/"
[[ -f VERSION ]] && cp VERSION "$APP_NAME_DIR/"

[[ -f "dist/${BIN_NAME}" ]] && cp "dist/${BIN_NAME}" "$APP_NAME_DIR/"
[[ -f "dist/${BIN_NAME}.exe" ]] && cp "dist/${BIN_NAME}.exe" "$APP_NAME_DIR/"

cat > "$APP_NAME_DIR/AVVIO_RAPIDO.txt" <<'NOTE'
Avvio rapido:
- Se trovi l'eseguibile EOQ_Pro / EOQ_Pro.exe: fai doppio clic.
- Altrimenti (versione Python):
  1) Apri il terminale in questa cartella
  2) Esegui:  python3 eoq_pro.py
Opzionali: pip install matplotlib reportlab
NOTE

rm -f "$OUT_ZIP" "${OUT_BASENAME}.zip"
zip -r "$OUT_ZIP" "$APP_NAME_DIR" >/dev/null
cp "$OUT_ZIP" "${OUT_BASENAME}.zip"

DATE="$(date +%F)"
{
  echo "## v${VERSION} — ${DATE}"
  echo "- Pacchetto demo generato (${OUT_ZIP})"
  echo "- Include: app Python, (eventuale) eseguibile, guida/README (se presenti), EULA, privacy, CSV di esempio, VERSION"
  echo
} >> CHANGELOG.md

echo "Creati: $OUT_ZIP e ${OUT_BASENAME}.zip"
