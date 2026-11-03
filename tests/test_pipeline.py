"""El pipeline completo sobre filas reales (corrida 20261103_1030), sin red: store temporal y HTML falso.

Orden: dedupe URL → dedupe título+empresa → excluir títulos/empresas → vistos → descripción SOLO para
LinkedIn sin texto (nunca evaluados primero) → remoto → LATAM → score → relevancia.
"""
import io
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent / "job1"))
from helpers import SeenStore, apply_filters  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "run_20261103_1030" / "results.csv"
HTML = (Path(__file__).parent / "fixtures" / "linkedin_job_4485431710.html").read_text(encoding="utf-8")


def load_fixture() -> pd.DataFrame:
    text = FIXTURE.read_text(encoding="utf-8")
    body = "\n".join(line for line in text.splitlines() if not line.startswith("#"))
    df = pd.read_csv(io.StringIO(body))
    df["description"] = df["description"].fillna("")
    return df.drop(columns=["match_score"])  # el pipeline lo recalcula


def run(tmp_path, df=None, fetch=None):
    store = SeenStore(tmp_path / "seen.json")
    calls = []

    def fake_fetch(job_id):
        calls.append(job_id)
        return HTML

    out, discards = apply_filters(df if df is not None else load_fixture(), seen_store=store, fetch=fetch or fake_fetch, sleep=lambda: None, run_id="20261103_1030")
    return out, discards, store, calls


def test_first_run_marks_everything_new_and_dedupes_by_title_and_company(tmp_path):
    out, _, _, _ = run(tmp_path)
    assert "is_new" in out.columns and out["is_new"].all()
    key = out["title"].str.strip().str.lower() + "|" + out["company"].str.strip().str.lower()
    assert key.is_unique


def test_descriptions_are_fetched_only_for_new_linkedin_rows(tmp_path):
    out, _, _, calls = run(tmp_path)
    linkedin = out[out["site"] == "linkedin"]
    assert len(calls) > 0
    assert linkedin["desc_fetched"].all()
    assert (linkedin["description"].str.len() > 1000).all()
    assert not out[out["site"] == "indeed"]["desc_fetched"].any()


def test_rows_with_description_never_pass_with_a_low_score(tmp_path):
    """Puede fallar: si la relevancia vuelve a aceptar 'score bajo + título dev', el Elixir entra."""
    df = load_fixture()
    elixir = df[df["site"] == "linkedin"].index[0]
    df.loc[elixir, "title"] = "Agentic Elixir Engineer - Remote"
    df.loc[elixir, "company"] = "Solo Elixir SpA"

    def fetch(job_id):
        return "<div class='show-more-less-html__markup'>Elixir, Phoenix, OTP, Erlang. Nada de JavaScript.</div>" \
            if job_id in df.loc[elixir, "job_url"] else HTML

    out, _, _, _ = run(tmp_path, df=df, fetch=fetch)
    assert "Solo Elixir SpA" not in set(out["company"])
    with_text = out[out["description"].str.strip() != ""]
    assert (with_text["match_score"] >= 2).all()


def test_second_run_after_mark_shown_has_no_new_jobs_and_fetches_nothing(tmp_path):
    out, _, store, _ = run(tmp_path)
    store.mark_shown(out, run_id="20261103_1030")
    again, _, _, calls = run(tmp_path)
    assert not again["is_new"].any()
    assert calls == []


def test_second_run_without_mark_shown_still_fetches_nothing_but_keeps_everything_new(tmp_path):
    """Si el email falló, la corrida siguiente los vuelve a mostrar como NUEVOS, pero las descripciones
    ya evaluadas no se vuelven a pedir: salen de la memoria."""
    out, _, _, first_calls = run(tmp_path)
    again, _, _, calls = run(tmp_path)
    assert calls == []
    assert again["is_new"].all()
    linkedin = again[again["site"] == "linkedin"]
    assert (linkedin["description"].str.len() > 1000).all()


def test_discard_groups_keep_their_labels(tmp_path):
    _, discards, _, _ = run(tmp_path)
    labels = [label for label, _ in discards]
    assert any("remote" in l for l in labels) and any("relevancia" in l for l in labels)
