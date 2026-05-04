import csv
import os
from pathlib import Path
import random
import re
import time

import pandas as pd
from jobspy import scrape_jobs
import resend

from config import (
    CONFIG,
    QUERIES_INDEED,
    QUERIES_LINKEDIN_FULL,
    QUERIES_LINKEDIN_LIGHT,
    SITES_REMOTE,
    SITES_HOURS,
    CORE_TECH,
    SECONDARY_TECH,
    INCOMPATIBLE_TECH,
    EXCLUDE_TITLE_KEYWORDS,
    EXCLUDE_COMPANIES,
    LATAM_KEYWORDS,
    TOTAL_CALLS,
)


# =============================================================================
# SCRAPING
# =============================================================================

def scrape_for_country(country: str, country_indeed: str, queries_linkedin: list, call_counter: list) -> list:
    """Scraping separado por sitio para respetar restricciones de cada API."""
    results = []

    # --- LinkedIn: queries específicas por país, con sleep anti-ban ---
    for query in queries_linkedin:
        call_counter[0] += 1
        label = f"[{call_counter[0]}/{TOTAL_CALLS}] {query} — {country} (LinkedIn)"
        print(f"  {label}...", end="", flush=True)
        t = time.time()
        try:
            jobs_linkedin = scrape_jobs(
                site_name=SITES_REMOTE,
                search_term=query,
                location=country,
                is_remote=True,
                results_wanted=CONFIG["results_wanted"],
                description_format="markdown",
                verbose=0,
            )
            jobs_linkedin["search_query"] = query
            jobs_linkedin["pais"] = country
            results.append(jobs_linkedin)
            elapsed = time.time() - t
            print(f" {len(jobs_linkedin)} resultados ({elapsed:.1f}s)")
        except Exception as e:
            print(f" ERROR: {e}")
        sleep_secs = random.choice([2, 4, 6, 9])
        print(f"    [sleep {sleep_secs}s anti-ban LinkedIn]")
        time.sleep(sleep_secs)

    # --- Indeed + Glassdoor: llamadas independientes para que un fallo de Glassdoor
    # no afecte a Indeed (ambos usan hours_old, incompatible con is_remote) ---
    for query in QUERIES_INDEED:
        for site in SITES_HOURS:
            call_counter[0] += 1
            label = f"[{call_counter[0]}/{TOTAL_CALLS}] {query} — {country} ({site.capitalize()})"
            print(f"  {label}...", end="", flush=True)
            t = time.time()
            try:
                jobs_site = scrape_jobs(
                    site_name=[site],
                    search_term=query,
                    location=country,
                    results_wanted=CONFIG["results_wanted"],
                    hours_old=CONFIG["hours_old"],
                    country_indeed=country_indeed,
                    description_format="markdown",
                    verbose=0,
                )
                jobs_site["search_query"] = query
                jobs_site["pais"] = country
                results.append(jobs_site)
                elapsed = time.time() - t
                print(f" {len(jobs_site)} resultados ({elapsed:.1f}s)")
            except Exception as e:
                print(f" ERROR: {e}")

    return results


def scrape_all_countries() -> list:
    """Ejecuta scraping en todos los países configurados."""
    all_jobs = []
    call_counter = [0]  # lista para mutabilidad por referencia

    # queries_linkedin=[] → skip LinkedIn para ese país (solo Indeed+Glassdoor)
    paises = [
        ("Chile",     "Chile",     QUERIES_LINKEDIN_FULL),   # LinkedIn + Indeed + Glassdoor
        ("Argentina", "Argentina", QUERIES_LINKEDIN_LIGHT),  # LinkedIn + Indeed + Glassdoor
        ("Uruguay",   "Uruguay",   []),                       # Solo Indeed + Glassdoor
        ("Peru",      "Peru",      []),                       # Solo Indeed + Glassdoor
    ]

    for pais_nombre, pais_indeed, queries_linkedin in paises:
        print(f"\n{'='*60}")
        print(f"  Buscando en: {pais_nombre} (LinkedIn: {len(queries_linkedin)}q, Indeed: {len(QUERIES_INDEED)}q)")
        print(f"{'='*60}")
        resultados = scrape_for_country(pais_nombre, pais_indeed, queries_linkedin, call_counter)
        all_jobs.extend(resultados)
        print(f"  → Bloques recolectados de {pais_nombre}: {len(resultados)}")

    return all_jobs


# =============================================================================
# PIPELINE: FILTROS + SCORING
#
# Flujo: dedupe → remote → títulos → empresas → score → relevancia
# Las funciones con _ son helpers internos usados por apply_filters().
# =============================================================================

def _is_absolute_senior(t: str) -> bool:
    """Excluye 'senior' y 'Sr' absolutos pero conserva 'semi senior' y 'semi-senior'."""
    if re.search(r"semi[\s-]+(senior|sr\.?)", t):
        return False
    if re.search(r"\bsenior\b", t):
        return True
    # "Sr Backend", "Sr. Developer", etc. (abreviatura de Senior)
    if re.search(r"\bsr\.?\s", t):
        return True
    return False


def _matches_excluded_title(title: str) -> bool:
    """Retorna True si el título contiene keywords excluidas."""
    t = str(title or "").lower()
    if any(word in t for word in EXCLUDE_TITLE_KEYWORDS):
        return True
    # "java" se excluye pero sin atrapar "javascript"
    if re.search(r"\bjava\b(?!script)", t):
        return True
    # "senior" / "Sr" se excluye pero NO "semi senior" ni "semi-senior"
    if _is_absolute_senior(t):
        return True
    # "Remote from Brazil / Mexico / etc." → puesto restringido a otro país
    if re.search(r"\bremote from\b", t):
        return True
    return False


def _matches_excluded_company(company: str) -> bool:
    """Retorna True si la empresa está en la lista de excluidas."""
    c = str(company or "").lower()
    return any(excluded in c for excluded in EXCLUDE_COMPANIES)


def _has_incompatible_tech(text: str) -> bool:
    """Retorna True si el texto tiene 2+ tecnologías incompatibles."""
    text_lower = str(text or "").lower()
    incompatible_count = sum(1 for tech in INCOMPATIBLE_TECH if tech in text_lower)
    return incompatible_count >= 2


def _calculate_match_score(row) -> int:
    """Puntaje basado en tecnologías encontradas en título y descripción.

    Título contiene tech  → peso × 2 (más específico).
    Descripción contiene  → peso × 1.
    2+ techs incompatibles en título → penalización -5.
    """
    title = str(row.get("title", "") or "").lower()
    description = str(row.get("description", "") or "").lower()
    score = 0
    for tech, weight in CORE_TECH.items():
        if tech in title:
            score += weight * 2
        elif tech in description:
            score += weight
    for tech, weight in SECONDARY_TECH.items():
        if tech in title:
            score += weight * 2
        elif tech in description:
            score += weight
    if _has_incompatible_tech(title):
        score = max(0, score - 5)
    return score


def _is_latam_open(row) -> bool:
    """Jobs de Chile siempre pasan. Jobs de otros países solo pasan si el título
    o descripción menciona apertura a LATAM, la región, o Chile explícitamente."""
    if str(row.get("pais", "")).lower() == "chile":
        return True
    text = (str(row.get("title", "") or "") + " " + str(row.get("description", "") or "")).lower()
    return any(kw in text for kw in LATAM_KEYWORDS)


def apply_filters(combined: pd.DataFrame) -> tuple:
    """Aplica todos los filtros en orden. Retorna (combined_filtrado, discard_groups)."""

    # Dedupe por URL
    before_dedup = len(combined)
    if "job_url" in combined.columns:
        combined = combined.drop_duplicates(subset=["job_url"], keep="first")
    else:
        combined = combined.drop_duplicates()
    print(f"[debug] Tras dedupe: {len(combined)} (descartados: {before_dedup - len(combined)})")

    # Filtro remote: LinkedIn ya viene filtrado con is_remote=True.
    # Indeed puede traer presenciales, filtramos por flag o keywords.
    # "home office" es el término más común en Chile/LATAM para trabajo remoto.
    remote_keywords = [
        "remote", "remoto", "teletrabajo", "full remote",
        "home office", "trabajo remoto", "desde casa", "desde tu casa",
        "trabajo en casa", "100% remoto", "100% remote",
    ]

    def is_likely_remote(row) -> bool:
        if row.get("is_remote") in (True, 1, "True", "true"):
            return True
        title    = str(row.get("title", "") or "").lower()
        desc     = str(row.get("description", "") or "").lower()
        location = str(row.get("location", "") or "").lower()
        return any(kw in f"{title} {desc} {location}" for kw in remote_keywords)

    mask_remote = combined.apply(is_likely_remote, axis=1)
    discarded_remote = combined[~mask_remote]
    combined = combined[mask_remote]
    print(f"[debug] Tras filtro remote: {len(combined)} (descartados: {len(discarded_remote)})")

    # Excluir títulos incompatibles
    mask_title = combined["title"].astype(str).apply(_matches_excluded_title)
    discarded_titles = combined[mask_title]
    combined = combined[~mask_title]
    print(f"[debug] Tras excluir títulos: {len(combined)} (descartados: {len(discarded_titles)})")

    # Excluir empresas
    mask_company = combined["company"].astype(str).apply(_matches_excluded_company)
    discarded_companies = combined[mask_company]
    combined = combined[~mask_company]
    print(f"[debug] Tras excluir empresas: {len(combined)} (descartados: {len(discarded_companies)})")

    # Filtro LATAM: jobs no-chilenos solo pasan si mencionan apertura regional
    mask_latam = combined.apply(_is_latam_open, axis=1)
    discarded_latam = combined[~mask_latam]
    combined = combined[mask_latam]
    print(f"[debug] Tras filtro LATAM: {len(combined)} (descartados: {len(discarded_latam)})")

    # Score
    combined["match_score"] = combined.apply(_calculate_match_score, axis=1)

    sort_cols = ["site", "match_score"]
    ascending = [True, False]
    if "date_posted" in combined.columns:
        sort_cols.append("date_posted")
        ascending.append(False)
    combined = combined.sort_values(by=sort_cols, ascending=ascending)

    # Filtro de relevancia
    mask_relevance = (
        (combined["match_score"] >= CONFIG["score_minimo"]) |
        (combined["title"].str.contains("fullstack|frontend|backend|developer|ingeniero|desarrollador", case=False, na=False))
    )
    discarded_relevance = combined[~mask_relevance]
    combined = combined[mask_relevance]
    print(f"[debug] Tras filtro relevancia: {len(combined)} (descartados: {len(discarded_relevance)})")

    discard_groups = [
        ("Filtro remote (no parece remoto)", discarded_remote),
        ("Filtro título (keyword excluida)", discarded_titles),
        ("Filtro empresa (empresa excluida)", discarded_companies),
        ("Filtro LATAM (job no-chileno sin apertura regional)", discarded_latam),
        ("Filtro relevancia (score bajo + título genérico)", discarded_relevance),
    ]

    return combined, discard_groups


# =============================================================================
# EXPORTACIÓN
# =============================================================================

def export_results(combined: pd.DataFrame, discard_groups: list, run_dir: Path, timestamp: str) -> Path:
    """Exporta los 3 archivos del run: results.csv, results.md, discarded.md.
    Retorna la ruta al archivo results.md (usado para el email).
    """

    # --- results.csv (datos completos con metadata de configuración) ---
    csv_path = run_dir / "results.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        f.write(f"# CONFIG_VERSION={CONFIG['version']}\n")
        f.write(f"# TIMESTAMP={timestamp}\n")
        f.write(f"# PAISES={','.join(CONFIG['paises'])}\n")
        f.write(f"# SITES_REMOTE={','.join(CONFIG['sites_con_remote_flag'])}\n")
        f.write(f"# SITES_HOURS={','.join(CONFIG['sites_con_hours_old'])}\n")
        f.write(f"# HOURS_OLD={CONFIG['hours_old']}\n")
        f.write(f"# SCORE_MINIMO={CONFIG['score_minimo']}\n")
        f.write(f"# QUERIES_LINKEDIN_FULL={len(QUERIES_LINKEDIN_FULL)}\n")
        f.write(f"# QUERIES_LINKEDIN_LIGHT={len(QUERIES_LINKEDIN_LIGHT)}\n")
        f.write(f"# QUERIES_INDEED={len(QUERIES_INDEED)}\n")
        f.write(f"# TOTAL_CALLS={TOTAL_CALLS}\n")
        f.write(f"# NOTA={CONFIG['nota']}\n")
        f.write(f"# TOTAL_RESULTADOS={len(combined)}\n")
        f.write("#\n")

    combined.to_csv(
        csv_path,
        mode="a",
        quoting=csv.QUOTE_NONNUMERIC,
        escapechar="\\",
        index=False,
    )

    # --- results.md (resumen legible con links) ---
    md_path = run_dir / "results.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# Resultados de busqueda — {timestamp}\n\n")
        f.write(f"**Total:** {len(combined)} trabajos")
        f.write(f" | **Score minimo:** {CONFIG['score_minimo']}")
        f.write(f" | **Paises:** {', '.join(CONFIG['paises'])}\n\n")
        f.write("---\n\n")
        for site in combined["site"].unique():
            site_df = combined[combined["site"] == site]
            f.write(f"## {site.capitalize()} ({len(site_df)} resultados)\n\n")
            f.write("| Score | Titulo | Empresa | Pais | Fecha |\n")
            f.write("|------:|--------|---------|------|-------|\n")
            for _, row in site_df.iterrows():
                score = int(row.get("match_score", 0))
                title = str(row.get("title", "") or "")
                url = str(row.get("job_url", "") or "")
                company = str(row.get("company", "") or "")
                pais = str(row.get("pais", "") or "")
                date = str(row.get("date_posted", "") or "")
                title_cell = f"[{title}]({url})" if url else title
                f.write(f"| {score} | {title_cell} | {company} | {pais} | {date} |\n")
            f.write("\n")

    # --- discarded.md (descartados para revisión manual) ---
    discarded_path = run_dir / "discarded.md"
    with open(discarded_path, "w", encoding="utf-8") as f:
        total_discarded = sum(len(df) for _, df in discard_groups)
        f.write(f"# Descartados — {timestamp}\n\n")
        f.write(f"**Total descartados:** {total_discarded}\n\n---\n\n")
        for label, df in discard_groups:
            if df.empty:
                continue
            f.write(f"## {label} ({len(df)})\n\n")
            f.write("| Titulo | Empresa | Pais | URL |\n")
            f.write("|--------|---------|------|-----|\n")
            for _, row in df.iterrows():
                title = str(row.get("title", "") or "")
                company = str(row.get("company", "") or "")
                pais = str(row.get("pais", "") or "")
                url = str(row.get("job_url", "") or "")
                title_cell = f"[{title}]({url})" if url else title
                f.write(f"| {title_cell} | {company} | {pais} |\n")
            f.write("\n")

    return md_path


# =============================================================================
# EMAIL
# =============================================================================

def send_email_report(run_id: str, results_md_path: Path, total: int) -> None:
    api_key = os.environ.get("RESEND_API_KEY")
    to_email = os.environ.get("RESEND_TO_EMAIL")
    if not api_key or not to_email:
        print("[email] Variables RESEND_API_KEY / RESEND_TO_EMAIL no configuradas, saltando.")
        return

    with open(results_md_path) as f:
        body = f.read()

    resend.api_key = api_key

    try:
        resend.Emails.send({
            "from": "job-radar@resend.dev",
            "to": to_email,
            "subject": f"⭐ Job Radar LATAM — {total} trabajos — {run_id}",
            "text": body,
            "headers": {
                "X-Priority": "1",
                "Importance": "high",
            },
        })
        print(f"[email] Enviado a {to_email}")
    except Exception as e:
        print(f"[email] Error al enviar: {e}")
