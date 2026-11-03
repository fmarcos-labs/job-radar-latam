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
