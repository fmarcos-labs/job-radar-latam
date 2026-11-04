"""Redirector de clics: GET /r/<token>?k=<clave>&u=<url> anota la clave en clicks.json y responde 302 a la URL.
Sin dependencias: biblioteca estándar, un archivo JSON, compartido por los dos radares.
"""
import json
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
from http.server import HTTPServer
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "job1"))
from redirector import Redirector, leer_clicks  # noqa: E402

TOKEN = "t0ken-de-prueba"
DESTINO = "https://www.getonbrd.com/jobs/programacion/x"


@pytest.fixture
def servidor(tmp_path):
    clicks = tmp_path / "clicks.json"
    handler = Redirector.con(token=TOKEN, clicks_file=clicks, ahora=lambda: "20261104_0930")
    httpd = HTTPServer(("127.0.0.1", 0), handler)
    hilo = threading.Thread(target=httpd.serve_forever, daemon=True)
    hilo.start()
    yield f"http://127.0.0.1:{httpd.server_port}", clicks
    httpd.shutdown()


def _get(url):
    class SinSeguir(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None

    opener = urllib.request.build_opener(SinSeguir)
    try:
        r = opener.open(url, timeout=5)
        return r.status, dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers)


def _link(base, token=TOKEN, k="dev full-stack|acme", u=DESTINO):
    return f"{base}/r/{token}?" + urllib.parse.urlencode({"k": k, "u": u})


def test_click_records_the_key_once_and_redirects_to_the_real_url(servidor):
    base, clicks = servidor
    status, headers = _get(_link(base))
    assert status == 302 and headers["Location"] == DESTINO
    assert leer_clicks(clicks) == {"dev full-stack|acme": "20261104_0930"}
    _get(_link(base))
    assert leer_clicks(clicks) == {"dev full-stack|acme": "20261104_0930"}, "la segunda apertura no pisa la primera"


def test_wrong_token_does_not_record_nor_redirect(servidor):
    base, clicks = servidor
    status, headers = _get(_link(base, token="otro"))
    assert status == 404 and "Location" not in headers
    assert leer_clicks(clicks) == {}


def test_only_http_destinations_are_redirected(servidor):
    base, clicks = servidor
    status, _ = _get(_link(base, u="javascript:alert(1)"))
    assert status == 400
    status, _ = _get(f"{base}/r/{TOKEN}?k=solo-clave")
    assert status == 400
    assert leer_clicks(clicks) == {}


def test_clicks_file_missing_or_corrupt_reads_as_empty(tmp_path):
    assert leer_clicks(tmp_path / "no-existe.json") == {}
    roto = tmp_path / "roto.json"
    roto.write_text("{", encoding="utf-8")
    assert leer_clicks(roto) == {}
    bien = tmp_path / "bien.json"
    bien.write_text(json.dumps({"a|b": "20261104_0930"}), encoding="utf-8")
    assert leer_clicks(bien) == {"a|b": "20261104_0930"}
