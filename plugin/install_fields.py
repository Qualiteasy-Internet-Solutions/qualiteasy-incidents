"""Instal·la el plugin oficial Fields 1.24.5 a GLPI 11 sense reconstruir Docker."""

from hashlib import sha256
from pathlib import Path
import subprocess
import tarfile
import tempfile
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parent.parent
URL = "https://github.com/pluginsGLPI/fields/releases/download/1.24.5/glpi-fields-1.24.5.tar.bz2"
SHA256 = "d932a550e48ffedeceeb5638cd4c116faddba312091e6bd29f8c0091a096c28e"


def compose(*args: str, capture: bool = False) -> str:
    result = subprocess.run(
        ["docker", "compose", *args], cwd=ROOT, check=True, text=True,
        capture_output=capture,
    )
    return result.stdout if capture else ""


with tempfile.TemporaryDirectory(prefix="qfields-") as temporary:
    directory = Path(temporary)
    archive = directory / "fields.tar.bz2"
    with urlopen(URL, timeout=30) as response:
        archive.write_bytes(response.read())
    if sha256(archive.read_bytes()).hexdigest() != SHA256:
        raise RuntimeError("El paquet Fields descarregat no coincideix amb el SHA-256 previst")

    with tarfile.open(archive, "r:bz2") as source:
        for member in source.getmembers():
            if not member.name.startswith("fields/") or member.issym() or member.islnk():
                raise RuntimeError(f"Entrada inesperada al paquet Fields: {member.name}")
        source.extractall(directory, filter="data")

    compose("cp", str(directory / "fields") + "/.", "glpi:/var/www/glpi/plugins/fields/")

state = compose("exec", "-T", "glpi", "php", "bin/console", "plugin:list", "--no-interaction", capture=True)
row = next((line for line in state.splitlines() if line.startswith("| fields ")), "")
if not row or "To update" in row:
    compose("exec", "-T", "glpi", "php", "bin/console", "plugin:install", "fields", "--no-interaction")
if "Enabled" not in row:
    compose("exec", "-T", "glpi", "php", "bin/console", "plugin:activate", "fields", "--no-interaction")
print("Fields 1.24.5 instal·lat i activat.")
