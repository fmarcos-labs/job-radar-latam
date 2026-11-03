"""Dedupe dentro de una corrida: el mismo aviso con 3 URLs distintas es UNA fila.

Medido en la corrida real 20261103_1030: 53 filas, 22 duplicados por (título, empresa).
"""
import io
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent / "job1"))
from helpers import dedupe_jobs  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "run_20261103_1030" / "results.csv"


def load_fixture() -> pd.DataFrame:
    text = FIXTURE.read_text(encoding="utf-8")
    body = "\n".join(line for line in text.splitlines() if not line.startswith("#"))
    return pd.read_csv(io.StringIO(body))


def test_fixture_has_53_rows_with_22_duplicates_by_title_company():
    df = load_fixture()
    key = df["title"].str.strip().str.lower() + "|" + df["company"].str.strip().str.lower()
    assert len(df) == 53
    assert len(df) - key.nunique() == 22


def test_dedupe_jobs_collapses_same_title_and_company_to_one_row():
    df = load_fixture()
    deduped = dedupe_jobs(df)
    key = deduped["title"].str.strip().str.lower() + "|" + deduped["company"].str.strip().str.lower()
    assert len(deduped) == 31
    assert key.is_unique


def test_dedupe_jobs_keeps_the_highest_score_of_the_group():
    df = pd.DataFrame(
        [
            {"title": "Backend Dev", "company": "Acme", "job_url": "u1", "match_score": 3},
            {"title": "backend dev ", "company": "ACME", "job_url": "u2", "match_score": 9},
        ]
    )
    deduped = dedupe_jobs(df)
    assert len(deduped) == 1
    assert int(deduped.iloc[0]["match_score"]) == 9
