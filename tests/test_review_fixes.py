"""Hallazgos del review adversarial del 03-11 (cada test nombra el suyo). Sin red."""
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "job1"))
import helpers  # noqa: E402
from helpers import (  # noqa: E402
    SeenStore,
    _http_get_linkedin_job,
    _job_key,
    apply_filters,
    dedupe_jobs,
    fetch_linkedin_descriptions,
    is_likely_remote,
    send_email_report,
)

HTML = (Path(__file__).parent / "fixtures" / "linkedin_job_4485431710.html").read_text(encoding="utf-8")


def li(title, company="Co", url_id=1, description="", location="Chile"):
    return {"site": "linkedin", "title": title, "company": company, "pais": "Chile", "location": location,
            "job_url": f"https://www.linkedin.com/jobs/view/{url_id}", "description": description}


# 1 · email fallido → NO se marca mostrado -------------------------------------------------------

def test_send_email_report_returns_false_when_resend_fails(monkeypatch, tmp_path):
    md = tmp_path / "results.md"; md.write_text("# x")
    monkeypatch.setenv("RESEND_API_KEY", "k"); monkeypatch.setenv("RESEND_TO_EMAIL", "a@b.c")
    monkeypatch.setattr(helpers.resend.Emails, "send", lambda payload: (_ for _ in ()).throw(RuntimeError("422")))
    assert send_email_report("r", md, 1) is False


def test_send_email_report_returns_false_without_config_and_true_on_success(monkeypatch, tmp_path):
    md = tmp_path / "results.md"; md.write_text("# x")
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    assert send_email_report("r", md, 1) is False
    monkeypatch.setenv("RESEND_API_KEY", "k"); monkeypatch.setenv("RESEND_TO_EMAIL", "a@b.c")
    monkeypatch.setattr(helpers.resend.Emails, "send", lambda payload: {"id": "ok"})
    assert send_email_report("r", md, 1) is True


# 2 · lo no bajado se reintenta en la corrida siguiente -------------------------------------------

def test_rows_left_without_description_by_the_cap_are_fetched_next_run(tmp_path):
    store = SeenStore(tmp_path / "seen.json")
    df = pd.DataFrame([li(f"Dev {i}", url_id=100 + i) for i in range(5)])
    calls = []
    apply_filters(df.copy(), seen_store=store, fetch=lambda j: (calls.append(j), HTML)[1], max_desc_fetch=2, sleep=lambda: None)
    assert len(calls) == 2
    calls.clear()
    apply_filters(df.copy(), seen_store=SeenStore(tmp_path / "seen.json"), fetch=lambda j: (calls.append(j), HTML)[1], max_desc_fetch=2, sleep=lambda: None)
    assert len(calls) == 2  # las 3 que faltaban van primero; el tope sigue acotando


# 3 · la señal "no remoto" de LinkedIn solo mira título y ubicación ------------------------------

@pytest.mark.parametrize("desc", ["100% remoto, no presencial", "apps hibridas (Ionic) y hybrid cloud",
                                  "Remote-first: no on-site required", "Entrevistas on-site opcionales"])
def test_linkedin_description_wording_does_not_make_a_job_not_remote(desc):
    assert is_likely_remote(li("Fullstack Engineer", description=desc)) is True


def test_linkedin_hybrid_in_location_is_not_remote():
    assert is_likely_remote(li("Fullstack Engineer", location="Santiago (Híbrido)")) is False


# 4 · el dedupe prefiere al gemelo sin señal de híbrido -------------------------------------------

def test_dedupe_keeps_the_remote_twin_over_the_hybrid_one():
    df = pd.DataFrame([li("Desarrollador Full Stack - Híbrido", url_id=1), li("Desarrollador Full Stack", url_id=2)])
    df["title"] = ["Desarrollador Full Stack", "Desarrollador Full Stack"]
    df.loc[0, "location"] = "Santiago (Híbrido)"
    kept = dedupe_jobs(df)
    assert len(kept) == 1 and kept.iloc[0]["job_url"].endswith("/2")


# 5 · seen.json corrupto no tumba la corrida; escritura atómica ---------------------------------

def test_corrupt_seen_file_is_set_aside_and_store_starts_empty(tmp_path, capsys):
    path = tmp_path / "seen.json"; path.write_text('{"a": {"first_run": "x"')  # truncado
    store = SeenStore(path)
    assert store.data == {}
    assert any(p.name.startswith("seen.json.corrupt-") for p in tmp_path.iterdir())
    assert "corrupt" in capsys.readouterr().out.lower()


def test_save_is_atomic_no_tmp_left_behind(tmp_path):
    store = SeenStore(tmp_path / "seen.json")
    store.remember(pd.DataFrame([li("A")]), run_id="r")
    assert sorted(p.name for p in tmp_path.iterdir()) == ["seen.json"]


# 6 · 0 filas no revienta ---------------------------------------------------------------------

def test_pipeline_with_everything_excluded_returns_empty_without_error(tmp_path):
    df = pd.DataFrame([li("QA Engineer", url_id=1), li("Senior Designer", url_id=2)])  # ambos excluidos por título
    out, discards = apply_filters(df, seen_store=SeenStore(tmp_path / "s.json"), fetch=lambda j: HTML, sleep=lambda: None)
    assert len(out) == 0 and any(len(d) == 2 for _, d in discards)


# 7 · LinkedIn 999 / authwall / fallas seguidas ---------------------------------------------------

class _Resp:
    def __init__(self, status, url, text="x"):
        self.status_code, self.url, self.text = status, url, text
    def raise_for_status(self):
        pass


def test_http_get_rejects_999_and_authwall(monkeypatch):
    monkeypatch.setattr(helpers.requests, "get", lambda *a, **k: _Resp(999, "https://www.linkedin.com/jobs/view/1"))
    with pytest.raises(RuntimeError):
        _http_get_linkedin_job("1")
    monkeypatch.setattr(helpers.requests, "get", lambda *a, **k: _Resp(200, "https://www.linkedin.com/authwall?x"))
    with pytest.raises(RuntimeError):
        _http_get_linkedin_job("1")


def test_fetch_stops_after_consecutive_failures():
    df = pd.DataFrame([li(f"Dev {i}", url_id=i) for i in range(20)])
    calls = []
    def always_fails(j):
        calls.append(j); raise RuntimeError("429")
    fetch_linkedin_descriptions(df, fetch=always_fails, max_fetch=20, sleep=lambda: None)
    assert len(calls) == helpers.MAX_CONSECUTIVE_FETCH_FAILURES


# 8/9 · vencimiento y tamaño de la memoria -------------------------------------------------------

def test_entries_older_than_max_age_expire_on_load(tmp_path):
    path = tmp_path / "seen.json"
    path.write_text(json.dumps({"viejo|co": {"first_run": "20260101_1030", "shown_run": "20260101_1030"},
                                "reciente|co": {"first_run": "20261103_1030"}}))
    store = SeenStore(path, today="20261103_1200", max_age_days=30)
    assert list(store.data) == ["reciente|co"]


def test_description_is_stored_only_for_linkedin(tmp_path):
    store = SeenStore(tmp_path / "seen.json")
    df = pd.DataFrame([li("A", url_id=1, description="texto li"),
                       {"site": "indeed", "title": "B", "company": "Co", "job_url": "u", "description": "texto indeed"}])
    store.remember(df, run_id="r")
    assert store.data["a|co"]["description"] == "texto li"
    assert "description" not in store.data["b|co"]


# 11 · NaN en las claves ----------------------------------------------------------------------

def test_job_key_treats_nan_and_none_as_empty():
    assert _job_key("Dev", float("nan")) == _job_key("Dev", None) == "dev|"
