#!/usr/bin/env bash
# Read-only target checks. Never installs, updates, restarts or changes a file.
set -euo pipefail
source /etc/os-release
[[ ${ID} == ubuntu && ${VERSION_ID} == 26.04 ]] || { printf '%s\n' 'Unexpected OS: stop and review.' >&2; exit 1; }
command -v python3.14 >/dev/null
python3.14 - <<'PY'
import ensurepip, sqlite3, ssl, sys, venv
from zoneinfo import ZoneInfo
assert sys.version_info[:3] == (3, 14, 4), "Expected confirmed Python 3.14.4; review, do not upgrade automatically"
assert sqlite3.sqlite_version_info >= (3, 31, 0)
print("Python:", sys.version.split()[0], "SQLite:", sqlite3.sqlite_version)
PY
command -v nginx >/dev/null
command -v ss >/dev/null
command -v systemctl >/dev/null
[[ -z $(ss -H -ltn 'sport = :8002') ]] || { printf '%s\n' '8002 is occupied. Do not stop its owner.' >&2; exit 1; }
available_kib=$(awk '/^MemAvailable:/ {print $2}' /proc/meminfo)
[[ ${available_kib} -ge 307200 ]] || { printf '%s\n' 'Less than 300 MiB available: stop and measure capacity.' >&2; exit 1; }
disk_kib=$(df -Pk /srv | awk 'NR==2 {print $4}')
[[ ${disk_kib} -ge 524288 ]] || { printf '%s\n' 'Less than 512 MiB free in /srv: stop and review.' >&2; exit 1; }
printf 'MemAvailable: %s KiB; /srv free: %s KiB\n' "${available_kib}" "${disk_kib}"
printf '%s\n' 'Preflight passed. Nginx vhosts, four AgroSmart hosts, DNS and certificates still need read-only inventory.'
