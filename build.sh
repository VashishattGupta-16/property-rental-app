#!/usr/bin/env bash
set -o errexit

python - <<'PY'
from pathlib import Path
p = Path('requirements.txt')
raw = p.read_bytes()
try:
    raw.decode('utf-8')
except UnicodeDecodeError:
    txt = raw.decode('utf-16')
    p.write_text(txt, encoding='utf-8')
PY

python -m pip install -r requirements.txt

# Build Tailwind CSS before collectstatic. If npm is not present, the compiled
# CSS must be committed at static/dist/output.css.
if command -v npm >/dev/null 2>&1; then
  npm ci --no-audit --no-fund
  npm run build:css
elif [ ! -f static/dist/output.css ]; then
  echo "npm is not installed and static/dist/output.css is missing"
  exit 1
fi

python manage.py collectstatic --no-input --clear
python manage.py migrate
