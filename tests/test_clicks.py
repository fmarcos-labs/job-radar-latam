"""Clics en el correo: el link pasa por el redirector solo si RADAR_CLICK_BASE está puesto; la columna
`abierto` sale de clicks.json por la misma clave que la memoria (título+empresa normalizados)."""
import json
import sys
import urllib.parse
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent / "job1"))
from helpers import _job_key, enlace_rastreado, marcar_abiertos, render_results_html  # noqa: E402

URL = "https://www.linkedin.com/jobs/view/123"


def test_without_base_the_link_is_the_real_url(monkeypatch):
    monkeypatch.delenv("RADAR_CLICK_BASE", raising=False)
    assert enlace_rastreado(URL, "dev|acme") == URL


def test_with_base_the_link_goes_through_the_redirector_with_key_and_url(monkeypatch):
    monkeypatch.setenv("RADAR_CLICK_BASE", "https://radar.fmarcos.dev/r/t0ken")
    link = enlace_rastreado(URL, "dev full-stack|acme")
    partes = urllib.parse.urlsplit(link)
    assert partes.scheme == "https" and partes.netloc == "radar.fmarcos.dev" and partes.path == "/r/t0ken"
    q = urllib.parse.parse_qs(partes.query)
    assert q["k"] == ["dev full-stack|acme"] and q["u"] == [URL]


def test_email_links_use_the_memory_key_of_each_row(monkeypatch):
    monkeypatch.setenv("RADAR_CLICK_BASE", "https://radar.fmarcos.dev/r/t0ken")
    df = pd.DataFrame([{"site": "linkedin", "title": "Dev Full-Stack", "company": "Acme", "job_url": URL, "match_score": 12, "is_new": True, "description": "x", "location": "Remote", "pais": "Chile", "date_posted": "2026-11-03"}])
    html = render_results_html(df, "20261104_1030", "v10.3", "abc1234")
    assert "radar.fmarcos.dev/r/t0ken?" in html and urllib.parse.quote(URL, safe="") in html
    assert urllib.parse.quote_plus(_job_key("Dev Full-Stack", "Acme")) in html


def test_marcar_abiertos_adds_a_column_from_clicks_json(tmp_path):
    clicks = tmp_path / "clicks.json"
    clicks.write_text(json.dumps({_job_key("Dev Full-Stack", "Acme"): "20261104_0930"}), encoding="utf-8")
    df = pd.DataFrame([{"title": "Dev Full-Stack", "company": "Acme"}, {"title": "Otro", "company": "Beta"}])
    out = marcar_abiertos(df, clicks)
    assert list(out["abierto"]) == ["20261104_0930", ""]
    assert list(marcar_abiertos(df, tmp_path / "no-existe.json")["abierto"]) == ["", ""]
