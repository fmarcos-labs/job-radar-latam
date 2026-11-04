"""GetOnBoard como fuente: el listado público HTML (sin login, sin API), todo desde la tarjeta.
Fixtures reales del 2026-11-03: 313 avisos de programación y 49 de IA.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent / "job1"))
from getonbrd import fecha_de_tarjeta, parse_listing, scrape_getonbrd  # noqa: E402
from helpers import SeenStore, apply_filters, dedupe_jobs, fecha_visible, is_likely_remote  # noqa: E402

FIX = Path(__file__).parent / "fixtures" / "getonbrd"
PROG = (FIX / "listado-programacion-CL-20261103.html").read_text(encoding="utf-8", errors="ignore")
IA = (FIX / "listado-machine-learning-ai-CL-20261103.html").read_text(encoding="utf-8", errors="ignore")
PAGINAS = {"programacion": PROG, "machine-learning-ai": IA}
HOY = "2026-11-03"


def _por_url(rows, fragmento):
    return next(r for r in rows if fragmento in r["job_url"])


def test_listing_has_every_card_with_the_fields_the_pipeline_needs():
    rows = parse_listing(PROG, hoy=HOY)
    assert len(rows) == 313
    primera = rows[0]
    assert primera["title"] == "Founding GTM Engineer"
    assert primera["company"] == "Hostop"
    assert primera["job_url"] == "https://www.getonbrd.com/jobs/programming/founding-gtm-engineer-hostop-remote"
    assert primera["is_remote"] is True
    assert primera["date_posted"] == "2026-11-03"
    assert primera["salary"] == "4500 - 6000 USD/month"
    assert primera["site"] == "getonbrd"
    segunda = rows[1]
    assert segunda["title"] == "Desarrollador/a Full-Stack" and segunda["company"] == "Financia Capital"
    assert segunda["is_remote"] is False and segunda["pais"] == "Chile"
    assert "Santiago" in segunda["location"] and "In-office" in segunda["location"]
    assert segunda["date_posted"] == "2026-10-27"


def test_card_summary_is_the_description_so_no_job_page_is_fetched():
    rows = parse_listing(PROG, hoy=HOY)
    con_texto = [r for r in rows if r["description"]]
    assert len(con_texto) == 313
    improving = _por_url(rows, "senior-frontend-software-engineer-improving")
    assert improving["description"].startswith("This role requires a Senior Frontend Software Engineer skilled in Vue.js")
    assert "candidates must reside in Chile, Argentina, Peru, Mexico or Costa Rica" in improving["description"]


def test_country_comes_from_the_card_because_the_country_filter_of_the_site_is_a_noop():
    rows = parse_listing(PROG, hoy=HOY) + parse_listing(IA, "machine-learning-ai", HOY)
    sin_chile = _por_url(rows, "ai-backend-engineer-improving")
    assert sin_chile["is_remote"] and sin_chile["pais"] == "Remote", "admite Argentina, Peru, Mexico o Costa Rica: no Chile"
    con_chile = _por_url(rows, "senior-frontend-software-engineer-improving")
    assert con_chile["pais"] == "Chile"
    mundo = next(r for r in rows if "anywhere in the world" in r["location"])
    assert mundo["pais"] == "Chile"
    region = next(r for r in rows if "South America" in r["location"])
    assert region["pais"] == "Chile"
    lima = next(r for r in rows if r["location"].startswith("Lima"))
    assert lima["pais"] == "Lima" and not lima["is_remote"]
    assert lima["location"].count("partly at the office") == 1, "el tooltip entra una sola vez"
    assert sum(1 for r in rows if r["pais"] == "Chile") == 311, "medido: ciudades chilenas + 53 remotos que nombran Chile + 79 «anywhere in the world» + región"


def test_listing_ia_category_and_company_is_clean():
    rows = parse_listing(IA, "machine-learning-ai", HOY)
    assert len(rows) == 49
    assert all(r["company"] == r["company"].strip() and "\n" not in r["company"] for r in rows)
    assert {r["search_query"] for r in rows} == {"getonbrd:machine-learning-ai"}


def test_card_dates_infer_the_year_without_crossing_today():
    assert fecha_de_tarjeta("Nov 03", hoy=HOY) == "2026-11-03"
    assert fecha_de_tarjeta("Oct 27", hoy=HOY) == "2026-10-27"
    assert fecha_de_tarjeta("Dec 20", hoy="2026-01-05") == "2025-12-20"
    assert fecha_de_tarjeta("", hoy=HOY) == ""


def test_scrape_returns_one_frame_with_both_categories_deduped_by_url():
    df = scrape_getonbrd(fetch_listing=lambda categoria: PAGINAS[categoria], hoy=HOY)
    assert len(df) == 362
    assert set(df["site"]) == {"getonbrd"}
    assert {"title", "company", "location", "job_url", "date_posted", "description", "is_remote", "pais", "search_query"} <= set(df.columns)
    assert df["job_url"].is_unique


def test_scrape_survives_one_category_failing():
    def fetch(categoria):
        if categoria == "programacion":
            raise RuntimeError("GetOnBoard respondió 503")
        return PAGINAS[categoria]

    df = scrape_getonbrd(fetch_listing=fetch, hoy=HOY, sleep=lambda: None)
    assert len(df) == 49


def test_remote_filter_trusts_the_explicit_modality_of_getonbrd():
    assert is_likely_remote({"site": "getonbrd", "is_remote": True, "title": "x", "description": "", "location": "Remote"})
    assert not is_likely_remote({"site": "getonbrd", "is_remote": False, "title": "x", "description": "", "location": "Santiago (Hybrid)"})


def test_pipeline_keeps_remote_open_to_chile_and_drops_the_rest_without_any_request(tmp_path):
    df = scrape_getonbrd(fetch_listing=lambda c: PAGINAS[c], hoy=HOY)
    pedidos = []
    out, descartes = apply_filters(df, seen_store=SeenStore(tmp_path / "seen.json"), fetch=lambda job_id: pedidos.append(job_id) or "", sleep=lambda: None, run_id=HOY)
    assert pedidos == [], "GetOnBoard no baja ninguna página de aviso"
    assert (out["site"] == "getonbrd").all() and (out["is_remote"]).all()
    assert (out["pais"] == "Chile").all()
    assert not out["job_url"].str.contains("ai-backend-engineer-improving").any(), "remoto que no admite Chile: fuera"
    latam = dict(descartes)["Filtro LATAM (job no-chileno sin apertura regional)"]
    assert latam["job_url"].str.contains("ai-backend-engineer-improving").any()
    assert (latam["pais"] != "Chile").all(), "ninguna keyword del resumen rescata a un remoto que no admite Chile"


def test_dedupe_keeps_one_row_when_linkedin_and_getonbrd_bring_the_same_job():
    df = pd.DataFrame(
        [
            {"site": "linkedin", "title": "Node.js Back-end Engineer (Senior)", "company": "ProntoPaga", "job_url": "l1", "match_score": 9},
            {"site": "getonbrd", "title": "Node.js Back-end Engineer (Senior)", "company": "ProntoPaga", "job_url": "g1", "match_score": 12},
        ]
    )
    assert len(dedupe_jobs(df)) == 1


def test_getonbrd_date_is_shown_without_a_year_because_the_card_has_none():
    assert fecha_visible({"site": "getonbrd", "date_posted": "2026-05-20"}) == "20-may"
    assert fecha_visible({"site": "linkedin", "date_posted": "2026-05-20"}) == "2026-05-20"
    assert fecha_visible({"site": "getonbrd", "date_posted": None}) == ""
