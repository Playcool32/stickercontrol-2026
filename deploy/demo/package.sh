#!/usr/bin/env bash
# Empaqueta StickerControl Demo Roura para publicar (en la PC, Git Bash). No toca el VPS.
#   bash deploy/demo/package.sh
# Resultado: release/<commit>/ con app.tar.gz (código del commit), build.tar.gz (frontend en modo demo) y SHA256SUMS.
#
# Fines de línea: `git archive` aplica core.autocrlf (en Windows, CRLF). El 2026-10-08 eso dejó CRLF en el código y
# las configuraciones del VPS (funcionaban, pero no eran idénticas al repo). Este script empaqueta sin conversión
# (-c core.autocrlf=false) y se detiene si algún archivo de texto del paquete contiene un retorno de carro.
set -euo pipefail
cd "$(dirname "$0")/../.."

if [ -n "$(git status --porcelain)" ]; then
  echo "El árbol tiene cambios sin commit: hacé commit antes de empaquetar." >&2
  exit 1
fi
ID=$(git rev-parse --short=7 HEAD)
OUT="release/$ID"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
rm -rf "$OUT" && mkdir -p "$OUT"

echo "== tests del backend"
(cd backend && .venv/Scripts/python.exe -m unittest discover -s tests 2>&1 | tail -1)

echo "== código ($ID), sin conversión de fines de línea"
git -c core.autocrlf=false -c core.eol=lf archive --format=tar.gz -o "$OUT/app.tar.gz" HEAD
mkdir -p "$TMP/app" && tar -xzf "$OUT/app.tar.gz" -C "$TMP/app"
# Control de CR solo en archivos de texto (un PNG puede contener ese byte). No se usa `grep $'\r'`: en Git Bash el
# CR del argumento llega vacío y el patrón coincide con todo. tr recibe la secuencia «\r» como texto y la interpreta.
CR_FILES=""
TEXT_FILES=0
while IFS= read -r f; do
  TEXT_FILES=$((TEXT_FILES + 1))
  n=$(tr -cd '\r' < "$f" | wc -c)
  [ "$n" -eq 0 ] || CR_FILES="$CR_FILES ${f#"$TMP"/app/}($n)"
done < <(grep -rIl . "$TMP/app")
[ -z "$CR_FILES" ] || { echo "Archivos con CR en el paquete:$CR_FILES" >&2; exit 1; }
echo "  sin CR ($TEXT_FILES archivos de texto, $(find "$TMP/app" -type f | wc -l) en total)"

echo "== frontend en modo demo (VITE_DEMO_MODE=true, VITE_BASE=/)"
# En Git Bash, MSYS convierte "/" en una ruta de Windows: se excluye VITE_BASE de esa conversión.
(cd frontend && MSYS2_ENV_CONV_EXCL=VITE_BASE VITE_DEMO_MODE=true VITE_BASE=/ npx --no-install vite build --outDir "$TMP/build" --emptyOutDir >/dev/null)
grep -q 'src="/assets/' "$TMP/build/index.html" || { echo "index.html sin base «/» (¿VITE_BASE convertido?)" >&2; exit 1; }
grep -q 'accounts.google.com/gsi' "$TMP/build/index.html" && { echo "el build de demo no debe cargar Google" >&2; exit 1; }
tar -czf "$OUT/build.tar.gz" -C "$TMP/build" .
echo "  $(tar -tzf "$OUT/build.tar.gz" | grep -vc '/$') archivos"

( cd "$OUT" && sha256sum app.tar.gz build.tar.gz | sed 's/ \*/  /' > SHA256SUMS )
CR=$(tr -cd '\r' < "$OUT/SHA256SUMS" | wc -c)
[ "$CR" -eq 0 ] || { echo "SHA256SUMS con CR" >&2; exit 1; }
echo "Versión $ID lista en $OUT"
cat "$OUT/SHA256SUMS"
