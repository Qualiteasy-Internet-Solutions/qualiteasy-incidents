"""Instal·la la paleta Qualiteasy al volum de GLPI, sense recrear contenidors."""

from base64 import b64encode
from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent.parent
THEME = Path(__file__).resolve().parent
template = (THEME / "qualiteasy.scss.in").read_text()
logo = b64encode((THEME / "qualiteasy-logo.png").read_bytes()).decode("ascii")
compiled = template.replace("__QUALITEASY_LOGO_URI__", f"data:image/png;base64,{logo}")
if compiled == template:
    raise SystemExit("Falta el marcador del logotip a la paleta")

with tempfile.NamedTemporaryFile(mode="w", suffix=".scss") as tmp:
    tmp.write(compiled)
    tmp.flush()
    subprocess.run(
        ["docker", "compose", "cp", tmp.name, "glpi:/var/glpi/files/_themes/qualiteasy.scss"],
        cwd=ROOT,
        check=True,
    )

subprocess.run(
    ["docker", "compose", "exec", "-T", "glpi", "php", "bin/console", "cache:clear", "--no-interaction"],
    cwd=ROOT,
    check=True,
)
print("Paleta instal·lada. Selecciona 'Qualiteasy' a les preferències de l'usuari.")
