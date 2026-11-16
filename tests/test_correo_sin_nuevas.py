"""Con 0 avisos NUEVOS no sale correo (medido: 2 de 18 correos eran vacíos), salvo que lleve un aviso de salud:
ese viaja en el mismo correo y es el único detector de v10.6. Sin red: Resend y las fuentes van simulados."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent / "job1"))
import helpers  # noqa: E402
import jobspy_search  # noqa: E402

DESCRIPCION = "Trabajo remoto. React, Node y TypeScript."


def aviso(site: str, n: int, **extra) -> dict:
    return {
        "site": site, "job_url": f"https://example.com/{site}/{n}", "title": f"Desarrollador React Node {site} {n}",
        "company": f"Acme {n}", "location": "Chile", "pais": "Chile", "date_posted": "2026-11-14",
        "description": DESCRIPCION, **extra,
    }


def preparar(monkeypatch, tmp_path, con_getonbrd: bool) -> list:
    enviados = []
    monkeypatch.setenv("RESEND_API_KEY", "clave-de-prueba")
    monkeypatch.setenv("RESEND_TO_EMAIL", "yo@example.com")
    monkeypatch.delenv("RADAR_CLICK_BASE", raising=False)
    monkeypatch.setattr(helpers.resend.Emails, "send", lambda payload: enviados.append(payload))
    jobspy_frames = [pd.DataFrame([aviso("linkedin", 1), aviso("indeed", 2)])]
    getonbrd = pd.DataFrame([aviso("getonbrd", 3, is_remote=True)]) if con_getonbrd else pd.DataFrame()
    monkeypatch.setattr(jobspy_search, "scrape_all_countries", lambda: list(jobspy_frames))
    monkeypatch.setattr(jobspy_search, "scrape_getonbrd", lambda: getonbrd)
    monkeypatch.setattr(jobspy_search, "JOB_DIR", tmp_path)
    monkeypatch.setattr(jobspy_search, "CLICKS_FILE", str(tmp_path / "clicks.json"))
    return enviados


def test_una_corrida_sana_sin_nuevas_no_manda_correo_pero_queda_en_el_log(monkeypatch, tmp_path, capsys):
    enviados = preparar(monkeypatch, tmp_path, con_getonbrd=True)

    jobspy_search.main()   # primera corrida: 3 nuevas, sale el correo y quedan mostradas
    assert len(enviados) == 1
    assert "3 nuevos / 3" in enviados[0]["subject"] and not enviados[0]["subject"].startswith("⚠")

    capsys.readouterr()
    jobspy_search.main()   # segunda corrida: todo ya visto

    assert len(enviados) == 1
    salida = capsys.readouterr().out
    assert "NUEVOS: 0" in salida and "0 nuevas" in salida
    corridas = [p for p in tmp_path.iterdir() if p.is_dir()]
    assert len(corridas) >= 1 and (corridas[0] / "results.csv").exists()


def test_sin_nuevas_pero_con_aviso_de_salud_el_correo_sale_igual(monkeypatch, tmp_path):
    enviados = preparar(monkeypatch, tmp_path, con_getonbrd=False)   # getonbrd en 0: aviso de fuente esencial

    jobspy_search.main()
    jobspy_search.main()   # sin nuevas, pero el aviso ⚠ sigue vigente

    assert len(enviados) == 2
    assert enviados[1]["subject"].startswith("⚠") and "0 nuevos / 2" in enviados[1]["subject"]
