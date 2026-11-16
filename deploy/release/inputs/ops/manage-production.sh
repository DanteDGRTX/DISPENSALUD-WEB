#!/usr/bin/env bash
# Only explicit management commands; does not start/stop a service or touch Nginx.
set -euo pipefail
[[ ${EUID} -eq 0 ]] || { printf '%s\n' 'Run as root; the environment file stays root-only.' >&2; exit 1; }
release_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
set -a
source /etc/dispensalud-web/web.env
set +a
export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 MALLOC_ARENA_MAX=2
[[ ${DJANGO_DEBUG:-} == 0 && ${DISPENSALUD_HOSTED_DEMO:-} == 0 && ${DISPENSALUD_FIREBASE_EMULATORS:-} == 0 ]]
[[ ${#DJANGO_SECRET_KEY} -ge 50 ]]
cd -- "${release_dir}/web"
exec runuser -u dispensalud-web -- "${release_dir}/.venv/bin/python" manage.py "$@"
