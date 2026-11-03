"""Memoria de vistos entre corridas: lo que ya se mostró no vuelve a salir como NUEVO.

Medido 31-10 → 03-11: 6 corridas = 317 filas por email, 43 avisos únicos (87 % repetido).
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent / "job1"))
from helpers import SeenStore  # noqa: E402


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
