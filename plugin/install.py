"""Copia i activa la fitxa municipal de prova a un GLPI 11 ja en marxa."""

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parent.parent
DEST = "/var/www/glpi/plugins/qincidents"


def compose(*args: str, capture: bool = False) -> str:
    result = subprocess.run(
        ["docker", "compose", *args],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=capture,
    )
    return result.stdout if capture else ""


compose("exec", "-T", "-u", "root", "glpi", "mkdir", "-p", DEST)
compose("cp", "plugin/qincidents/.", f"glpi:{DEST}/")
for filename in ("setup.php", "hook.php", "front/fiche.php"):
    compose("exec", "-T", "glpi", "php", "-l", f"plugins/qincidents/{filename}")
state = compose("exec", "-T", "glpi", "php", "bin/console", "plugin:list", "--no-interaction", capture=True)
row = next((line for line in state.splitlines() if line.startswith("| qincidents ")), "")
if not row or "To update" in row:
    compose("exec", "-T", "glpi", "php", "bin/console", "plugin:install", "qincidents", "--no-interaction")
if "Enabled" not in row:
    compose("exec", "-T", "glpi", "php", "bin/console", "plugin:activate", "qincidents", "--no-interaction")
compose("exec", "-T", "glpi", "php", "bin/console", "cache:clear", "--no-interaction")
print("Fitxa Qualiteasy instal·lada sense reconstruir Docker.")
