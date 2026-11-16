"""Memoria de vistos entre corridas: lo que ya se mostró no vuelve a salir como NUEVO.

Medido 31-10 → 03-11: 6 corridas = 317 filas por email, 43 avisos únicos (87 % repetido).
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent / "job1"))
from helpers import SeenStore, apply_filters  # noqa: E402

LINKEDIN_HTML = (Path(__file__).parent / "fixtures" / "linkedin_job_4485431710.html").read_text(encoding="utf-8")


def jobs(*pairs) -> pd.DataFrame:
    return pd.DataFrame([{"site": "linkedin", "title": t, "company": c, "job_url": f"u-{t}-{c}"} for t, c in pairs])


def test_first_run_everything_is_new(tmp_path):
    store = SeenStore(tmp_path / "seen.json")
    df = jobs(("Backend Dev", "Acme"), ("Fullstack", "Kraken"))
    assert store.split_new(df)[0].shape[0] == 2


def test_remembered_jobs_are_not_new_on_the_next_run(tmp_path):
    path = tmp_path / "seen.json"
    first = SeenStore(path)
    df = jobs(("Backend Dev", "Acme"), ("Fullstack", "Kraken"))
    first.remember(df, run_id="20261103_1030")

    second = SeenStore(path)  # otra corrida: se relee del disco
    new, seen = second.split_new(jobs(("backend dev ", "ACME"), ("Fullstack", "Kraken"), ("Python Dev", "Nuevo SA")))
    assert list(new["company"]) == ["Nuevo SA"]
    assert len(seen) == 2


def test_remember_persists_first_run_id_and_does_not_overwrite_it(tmp_path):
    path = tmp_path / "seen.json"
    store = SeenStore(path)
    store.remember(jobs(("Backend Dev", "Acme")), run_id="20261101_1030")
    store.remember(jobs(("Backend Dev", "Acme")), run_id="20261103_1030")
    data = json.loads(path.read_text())
    assert data["backend dev|acme"]["first_run"] == "20261101_1030"


def test_missing_file_means_empty_store(tmp_path):
    store = SeenStore(tmp_path / "no-existe.json")
    new, seen = store.split_new(jobs(("X", "Y")))
    assert len(new) == 1 and len(seen) == 0


def test_evaluated_but_not_shown_keeps_its_description_for_the_next_run(tmp_path):
    """Un aviso descartado en la corrida 1 no vuelve a gastar un request ni entra vacío en la 2."""
    path = tmp_path / "seen.json"
    first = SeenStore(path)
    evaluated = jobs(("Backend Dev", "Acme"))
    evaluated["description"] = "texto largo bajado de linkedin"
    first.remember(evaluated, run_id="20261103_1030")  # evaluado, no mostrado

    second = SeenStore(path)
    df = jobs(("Backend Dev", "Acme"))
    df["description"] = ""
    filled = second.fill_descriptions(df)
    assert filled.loc[0, "description"] == "texto largo bajado de linkedin"
    assert second.was_shown(df).tolist() == [False]


def test_mark_shown_makes_the_job_not_new_anymore(tmp_path):
    path = tmp_path / "seen.json"
    store = SeenStore(path)
    df = jobs(("Backend Dev", "Acme"), ("Fullstack", "Kraken"))
    store.remember(df, run_id="20261103_1030")
    store.mark_shown(df.iloc[[0]], run_id="20261103_1030")

    again = SeenStore(path)
    assert again.was_shown(df).tolist() == [True, False]
    data = json.loads(path.read_text())
    assert data["backend dev|acme"]["shown_run"] == "20261103_1030"
    assert "shown_run" not in data["fullstack|kraken"]


def with_description(df: pd.DataFrame, text: str) -> pd.DataFrame:
    return df.assign(description=text)


def test_job_shown_without_description_comes_back_once_when_it_arrives_with_text(tmp_path):
    """Una oferta de NTT salió sin descripción, quedó como vista y nunca volvió con ella."""
    path = tmp_path / "seen.json"
    df = jobs(("Backend Dev", "NTT"))
    store = SeenStore(path)
    store.remember(with_description(df, ""), run_id="20261110_1030")
    store.mark_shown(with_description(df, ""), run_id="20261110_1030")
    assert json.loads(path.read_text())["backend dev|ntt"]["shown_no_desc"] is True

    later = SeenStore(path)
    assert later.was_shown(with_description(df, "")).tolist() == [True]                 # sigue sin texto: no vuelve
    assert later.was_shown(with_description(df, "React y Node")).tolist() == [False]    # llegó con texto: se reevalúa

    later.mark_shown(with_description(df, "React y Node"), run_id="20261111_1030")
    again = SeenStore(path)
    assert again.was_shown(with_description(df, "React y Node")).tolist() == [True]     # una sola vez
    assert json.loads(path.read_text())["backend dev|ntt"]["shown_run"] == "20261110_1030"


def test_job_shown_with_description_never_comes_back(tmp_path):
    path = tmp_path / "seen.json"
    df = with_description(jobs(("Backend Dev", "Acme")), "React y Node")
    store = SeenStore(path)
    store.mark_shown(df, run_id="20261110_1030")
    assert SeenStore(path).was_shown(df).tolist() == [True]


def test_legacy_seen_records_without_the_new_field_keep_working(tmp_path):
    path = tmp_path / "seen.json"
    path.write_text(json.dumps({"backend dev|acme": {"first_run": "20261110_1030", "shown_run": "20261110_1030"}}))
    df = with_description(jobs(("Backend Dev", "Acme")), "React y Node")
    assert SeenStore(path).was_shown(df).tolist() == [True]


def test_pipeline_shows_again_a_job_whose_description_arrives_in_a_later_run(tmp_path):
    path = tmp_path / "seen.json"
    row = {"site": "linkedin", "title": "Fullstack Developer", "company": "NTT", "pais": "Chile", "location": "Chile",
           "job_url": "https://www.linkedin.com/jobs/view/777", "description": ""}

    def blocked(job_id):
        raise RuntimeError("LinkedIn respondió 429")

    first, _ = apply_filters(pd.DataFrame([row]), seen_store=SeenStore(path), fetch=blocked, sleep=lambda: None, run_id="20261110_1030")
    assert first["is_new"].tolist() == [True]
    SeenStore(path).mark_shown(first, run_id="20261110_1030")

    second, _ = apply_filters(pd.DataFrame([row]), seen_store=SeenStore(path), fetch=lambda job_id: LINKEDIN_HTML, sleep=lambda: None, run_id="20261111_1030")
    assert second["is_new"].tolist() == [True]
    SeenStore(path).mark_shown(second, run_id="20261111_1030")

    third, _ = apply_filters(pd.DataFrame([row]), seen_store=SeenStore(path), fetch=lambda job_id: LINKEDIN_HTML, sleep=lambda: None, run_id="20261112_1030")
    assert third["is_new"].tolist() == [False]
