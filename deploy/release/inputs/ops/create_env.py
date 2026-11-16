"""Run only on the target as root. Never overwrites a pre-existing key."""
import os
from pathlib import Path
import secrets
import sys

if sys.platform != "linux" or os.geteuid() != 0:
    raise SystemExit("Run on the target Linux host as root, after authorization.")
target = Path("/etc/dispensalud-web/web.env")
example = Path(__file__).with_name("web.env.example").read_text(encoding="utf-8")
os.umask(0o077)
with target.open("x", encoding="utf-8", newline="\n") as output:
    output.write(example.rstrip() + "\nDJANGO_SECRET_KEY=" + secrets.token_urlsafe(64) + "\n")
os.chmod(target, 0o600)
print("Created root-only environment file; secret not displayed. Preserve it across releases.")
