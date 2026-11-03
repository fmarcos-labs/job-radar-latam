"""Descripción de LinkedIn: JobSpy no la baja salvo `linkedin_fetch_description=True` y el script
nunca lo pasó → 100 % de las filas de LinkedIn llegaban vacías (medido 03-11). Se baja SOLO para los
avisos nuevos, con tope y sleep, y el HTTP se inyecta para testear sin red."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent / "job1"))
from helpers import fetch_linkedin_descriptions, parse_linkedin_description  # noqa: E402

HTML = (Path(__file__).parent / "fixtures" / "linkedin_job_4485431710.html").read_text(encoding="utf-8")


def test_parse_extracts_the_job_description_as_text():
    text = parse_linkedin_description(HTML)
    assert text is not None
    assert len(text) > 1000
    assert "Kraken" in text


def test_parse_returns_none_when_the_page_has_no_description_block():
    assert parse_linkedin_description("<html><body>Sign in to LinkedIn</body></html>") is None


def linkedin_rows(n: int, with_description: bool = False) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "site": "linkedin",
                "title": f"Dev {i}",
                "company": "Co",
                "job_url": f"https://www.linkedin.com/jobs/view/{1000 + i}",
                "description": "ya tenía texto" if with_description else "",
            }
            for i in range(n)
        ]
    )


def test_fetch_fills_description_only_for_linkedin_rows_without_text():
    df = pd.concat([linkedin_rows(2), linkedin_rows(1, with_description=True)], ignore_index=True)
    df.loc[3] = {"site": "indeed", "title": "X", "company": "Y", "job_url": "https://cl.indeed.com/viewjob?jk=1", "description": ""}
    calls = []

    def fake_fetch(job_id: str) -> str:
        calls.append(job_id)
        return HTML

    out = fetch_linkedin_descriptions(df, fetch=fake_fetch, max_fetch=10, sleep=lambda: None)
    assert calls == ["1000", "1001"]
    assert all("Kraken" in d for d in out.loc[[0, 1], "description"])
    assert out.loc[2, "description"] == "ya tenía texto"
    assert out.loc[3, "description"] == ""


def test_fetch_respects_the_hard_cap_and_marks_the_rest():
    df = linkedin_rows(5)
    calls = []
    out = fetch_linkedin_descriptions(df, fetch=lambda jid: (calls.append(jid), HTML)[1], max_fetch=2, sleep=lambda: None)
    assert len(calls) == 2
    assert list(out["desc_fetched"]) == [True, True, False, False, False]


def test_fetch_survives_a_failing_request_and_keeps_going():
    df = linkedin_rows(3)

    def flaky(job_id: str) -> str:
        if job_id == "1001":
            raise RuntimeError("429 Too Many Requests")
        return HTML

    out = fetch_linkedin_descriptions(df, fetch=flaky, max_fetch=10, sleep=lambda: None)
    assert list(out["desc_fetched"]) == [True, False, True]
    assert out.loc[1, "description"] == ""
