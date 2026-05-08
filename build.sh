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

# Build Tailwind CSS (required because WhiteNoise's manifest storage will 500
# in production if a referenced static file doesn't exist).
npm ci --no-audit --no-fund
npm run build:css

python manage.py collectstatic --no-input --clear
python manage.py migrate
