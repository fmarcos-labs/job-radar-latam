"""Lo que llega por email: NUEVOS arriba, el resto resumido, y la iteración identificable.

Medido 03-11: cada email traía ~30 filas con 2-6 nuevos escondidos; y 3 comportamientos distintos
corrieron bajo 2 etiquetas de versión (los commits entre bumps no se veían en el email).
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent / "job1"))
from helpers import build_email_subject, export_results, read_git_sha  # noqa: E402


def test_subject_shows_new_count_total_version_and_sha():
    subject = build_email_subject(new_count=12, total=53, version="v10.0", sha="a1b2c3d", run_id="20261103_1030")
    assert subject == "⭐ Job Radar LATAM — 12 nuevos / 53 — v10.0 (a1b2c3d) — 20261103_1030"


def test_read_git_sha_prefers_the_file_written_by_the_deploy(tmp_path):
    (tmp_path / "GIT_SHA").write_text("deadbee\n")
    assert read_git_sha(tmp_path) == "deadbee"


def test_read_git_sha_without_file_and_without_repo_is_explicit(tmp_path):
    assert read_git_sha(tmp_path) == "sin-sha"


def sample_jobs() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"site": "indeed", "title": "Viejo A", "company": "Acme", "pais": "Chile", "date_posted": "2026-11-01", "job_url": "u1", "match_score": 9, "is_new": False},
            {"site": "linkedin", "title": "Nuevo B", "company": "Kraken", "pais": "Chile", "date_posted": "2026-11-03", "job_url": "u2", "match_score": 4, "is_new": True},
            {"site": "linkedin", "title": "Nuevo C", "company": "Cumplo", "pais": "Chile", "date_posted": "2026-11-03", "job_url": "u3", "match_score": 12, "is_new": True},
        ]
    )


def test_results_md_opens_with_new_jobs_sorted_by_score_and_counts_the_seen_ones(tmp_path):
    md_path = export_results(sample_jobs(), [], tmp_path, "20261103_1030", version="v10.0", sha="a1b2c3d")
    md = md_path.read_text(encoding="utf-8")
    nuevos = md.index("## NUEVOS (2)")
    assert nuevos < md.index("## Indeed")
    assert md.index("Nuevo C") < md.index("Nuevo B")  # score 12 antes que 4
    assert "ya vistos en corridas anteriores: 1" in md
    assert "v10.0 (a1b2c3d)" in md


def test_results_csv_header_records_the_sha(tmp_path):
    export_results(sample_jobs(), [], tmp_path, "20261103_1030", version="v10.0", sha="a1b2c3d")
    header = (tmp_path / "results.csv").read_text(encoding="utf-8").splitlines()[:16]
    assert "# GIT_SHA=a1b2c3d" in header
    assert "# CONFIG_VERSION=v10.0" in header


# --- correo HTML: el score pesa visualmente, nada se oculta ---
from helpers import render_results_html  # noqa: E402


def sample_for_html() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"site": "linkedin", "title": "Fuerte", "company": "A", "pais": "Chile", "date_posted": "2026-11-03", "job_url": "u1", "match_score": 24, "description": "react node", "is_new": True},
            {"site": "indeed", "title": "Medio", "company": "B", "pais": "Chile", "date_posted": "2026-11-03", "job_url": "u2", "match_score": 12, "description": "react", "is_new": True},
            {"site": "linkedin", "title": "Flojo", "company": "C", "pais": "Peru", "date_posted": "2026-11-02", "job_url": "u3", "match_score": 3, "description": "x", "is_new": True},
            {"site": "linkedin", "title": "Sin texto", "company": "D", "pais": "Chile", "date_posted": "2026-11-02", "job_url": "u4", "match_score": 0, "description": "", "is_new": True},
            {"site": "indeed", "title": "Visto", "company": "E", "pais": "Chile", "date_posted": "2026-11-01", "job_url": "u5", "match_score": 30, "description": "node", "is_new": False},
            {"site": "indeed", "title": "Sin fecha", "company": None, "pais": "Chile", "date_posted": float("nan"), "job_url": "u6", "match_score": 2, "description": "x", "is_new": True},
        ]
    )


def test_html_keeps_every_new_row_in_score_order_and_weighs_the_score(tmp_path):
    html = render_results_html(sample_for_html(), timestamp="20261103_1030", version="v10.1", sha="abc1234", fuerte=20, medio=10)
    filas = [l for l in html.splitlines() if 'class="fila ' in l]
    assert len(filas) == 5, "las 5 nuevas, ninguna oculta; la vista no va"
    assert "Visto" not in html
    assert html.index("Fuerte") < html.index("Medio") < html.index("Flojo") < html.index("Sin texto")
    assert 'class="fila fuerte"' in filas[0] and "<b>Fuerte</b>" in filas[0]
    assert 'class="fila medio"' in filas[1]
    assert all('class="fila flojo"' in fila for fila in filas[2:])
    assert "s/d" in filas[4], "score 0 sin descripción se declara, no parece mal match"
    assert "s/d" not in filas[2] and "s/d" not in filas[3]
    assert "NUEVOS (5)" in html and "ya vistos: 1" in html and "v10.1 (abc1234)" in html
    assert "nan" not in html, "una celda vacía se ve vacía, no «nan»"
    assert "<button" not in html


def test_export_writes_results_html_next_to_md(tmp_path):
    export_results(sample_for_html(), [], tmp_path, "20261103_1030", version="v10.1", sha="abc1234")
    html = (tmp_path / "results.html").read_text(encoding="utf-8")
    assert "NUEVOS (5)" in html and 'href="u1"' in html
