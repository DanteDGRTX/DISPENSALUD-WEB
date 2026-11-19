#!/usr/bin/env bash
set -euo pipefail
project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"
command -v java >/dev/null
command -v mvn >/dev/null
command -v node >/dev/null
python3 - <<'PY'
import socket
for port in (8000,8091,8092):
    with socket.socket() as check:
        try: check.bind(("127.0.0.1",port))
        except OSError: raise SystemExit(f"Puerto {port} ocupado; no se modifica el proceso existente.")
PY
mvn -B -f spring/pom.xml verify
if [[ ! -x web/.venv/bin/python ]]; then python3 -m venv web/.venv; fi
web/.venv/bin/python -m pip install -r web/requirements.txt
(cd web && npm ci --no-audit --no-fund && npm run build)
export DISPENSALUD_SUPERVISION_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
export DISPENSALUD_SPRING_URL=http://127.0.0.1:8091
supervision_pid="" portal_pid=""
cleanup() {
  if [[ -n "$portal_pid" ]]; then kill "$portal_pid" 2>/dev/null || true; fi
  if [[ -n "$supervision_pid" ]]; then kill "$supervision_pid" 2>/dev/null || true; fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
java -jar spring/supervision/target/supervision-1.0.0-SNAPSHOT.jar & supervision_pid=$!
java -jar spring/portal/target/portal-1.0.0-SNAPSHOT.jar & portal_pid=$!
python3 - <<'PY'
import json, time, urllib.request
for port in (8091,8092):
    for attempt in range(60):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/health",timeout=1) as response:
                if json.load(response)["status"]=="ok": break
        except (OSError,ValueError): time.sleep(.5)
    else: raise SystemExit(f"El servicio {port} no estuvo listo.")
PY
(cd web && .venv/bin/python manage.py migrate --noinput && .venv/bin/python manage.py runserver 127.0.0.1:8000 --noreload)
