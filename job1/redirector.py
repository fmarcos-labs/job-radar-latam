"""Redirector de clics del correo: GET /r/<token>?k=<clave>&u=<url>.

Anota la clave (título+empresa normalizados, la misma de seen.json) con la hora de la PRIMERA apertura
en clicks.json y responde 302 a la URL real. Solo biblioteca estándar, un archivo JSON compartido por
los dos radares; el radar lo lee para la columna `abierto`. Si este servicio está caído el link no
abre: la URL real viaja en el link y el 302 es lo único que hace.

    RADAR_CLICK_TOKEN=... RADAR_CLICKS_FILE=/ruta/clicks.json python redirector.py [puerto]
"""
import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

PUERTO_DEFAULT = 3008
ESQUEMAS = ("http://", "https://")


def leer_clicks(path) -> dict:
    """{clave: primera_apertura}. Sin archivo o JSON roto, vacío: un redirector no tira la corrida del radar."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _guardar(path, data: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


class Redirector(BaseHTTPRequestHandler):
    token = ""
    clicks_file = Path("clicks.json")
    ahora = staticmethod(lambda: time.strftime("%Y%m%d_%H%M"))

    @classmethod
    def con(cls, token: str, clicks_file, ahora=None):
        attrs = {"token": token, "clicks_file": Path(clicks_file)}
        if ahora:
            attrs["ahora"] = staticmethod(ahora)
        return type("RedirectorConfigurado", (cls,), attrs)

    def do_GET(self):
        partes = urlsplit(self.path)
        if partes.path != f"/r/{self.token}" or not self.token:
            return self._responder(404)
        q = parse_qs(partes.query)
        clave = (q.get("k") or [""])[0].strip()
        destino = (q.get("u") or [""])[0].strip()
        if not clave or not destino.startswith(ESQUEMAS):
            return self._responder(400)
        clicks = leer_clicks(self.clicks_file)
        if clave not in clicks:
            clicks[clave] = self.ahora()
            _guardar(self.clicks_file, clicks)
        self.send_response(302)
        self.send_header("Location", destino)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def _responder(self, codigo: int):
        self.send_response(codigo)
        self.end_headers()

    def log_message(self, format, *args):
        sys.stdout.write(f"{self.ahora()} {self.address_string()} {format % args}\n")


def main():
    token = os.environ.get("RADAR_CLICK_TOKEN", "")
    if not token:
        sys.exit("falta RADAR_CLICK_TOKEN")
    clicks_file = os.environ.get("RADAR_CLICKS_FILE", str(Path(__file__).parent / "clicks.json"))
    puerto = int(sys.argv[1]) if len(sys.argv) > 1 else PUERTO_DEFAULT
    handler = Redirector.con(token=token, clicks_file=clicks_file)
    print(f"redirector en 127.0.0.1:{puerto} → {clicks_file}", flush=True)
    HTTPServer(("127.0.0.1", puerto), handler).serve_forever()


if __name__ == "__main__":
    main()
