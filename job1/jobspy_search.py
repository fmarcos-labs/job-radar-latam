import csv
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from pathlib import Path
import random
import re
import smtplib
import time

import pandas as pd
from jobspy import scrape_jobs

# =============================================================================
# CONFIGURACIÓN ACTIVA - se guarda en cada CSV para poder iterar
# =============================================================================
CONFIG = {
    "version": "v7.7",
    "paises": ["Chile", "Argentina", "Colombia"],
    "sites_con_remote_flag": ["linkedin"],       # usan is_remote=True
    "sites_con_hours_old": ["indeed"],            # usan hours_old (incompatible con is_remote)
    "sites_eliminados": ["google", "zip_recruiter"],  # no funcionan para Chile/LATAM
    "hours_old": 168,
    "results_wanted": 50,
    "score_minimo": 2,
    "nota": "v7.6: Excluir 'Sr' (abreviatura senior). Excluir 'remote from [pais]' (puesto restringido a otro país). Excluir IoT.",
}

# LinkedIn Chile: 12 queries curadas (las redundantes se eliminaron tras análisis de duplicados)
QUERIES_LINKEDIN_FULL = [
    "fullstack developer typescript",
    "react developer",
    "nodejs developer",
    "python developer",
    "flutter developer",
    "remote developer latam",
    "backend developer",
    "frontend developer",
    "ingeniero fullstack",
    "desarrollador fullstack",
    "desarrollador react",
    "desarrollador freelance",
]

# LinkedIn Argentina/Colombia: 6 queries genéricas que cubren el espectro más amplio
QUERIES_LINKEDIN_LIGHT = [
    "fullstack developer typescript",
    "react developer",
    "backend developer",
    "remote developer latam",
    "desarrollador fullstack",
    "ingeniero fullstack",
]

# Indeed: todas las queries (rápido ~1s/call, sin riesgo de ban)
QUERIES_INDEED = [
    "fullstack developer typescript",
    "react developer",
    "nextjs developer",
    "frontend developer typescript",
    "nodejs developer",
    "python developer",
    "django developer",
    "fastapi developer",
    "backend python developer",
    "flutter developer",
    "remote developer latam",
    "fullstack remote latam",
    "react remote latam",
    "senior fullstack developer",
    "graphql developer",
    "backend developer",
    "frontend developer",
    "ai engineer",
    "ingeniero backend",
    "ingeniero fullstack",
    "desarrollador backend",
    "desarrollador fullstack",
    "desarrollador python",
    "desarrollador react",
    "freelance developer",
    "fullstack freelance",
    "desarrollador freelance",
]

# Solo Indeed y LinkedIn (Google y ZipRecruiter no funcionan para LATAM)
SITES_REMOTE = ["linkedin"]   # soportan is_remote sin conflicto
SITES_HOURS  = ["indeed"]     # requieren hours_old, incompatible con is_remote

CORE_TECH = {
    # JavaScript/TypeScript - stack principal
    "typescript": 4,
    "react": 4,
    "next.js": 4,
    "nextjs": 4,
    "node.js": 4,
    "nodejs": 4,
    "nestjs": 3,
    "express": 3,
    # Python - segunda habilidad fuerte
    "python": 2,
    "django": 2,
    "fastapi": 2,
    # Complementarios
    "graphql": 2,
    "flutter": 2,
}

SECONDARY_TECH = {
    "puppeteer": 1,
    "scraping": 1,
    "strapi": 1,
    "supabase": 1,
    "prisma": 1,
    "postgresql": 1,
    "postgres": 1,
    "websocket": 1,
    "socket.io": 1,
    "api": 1,
    "rest": 1,
    "openai": 2,
}

INCOMPATIBLE_TECH = [
    "elixir", "ruby", "rails", "php", "laravel",
    "java", "c#", ".net", "swift", "kotlin",
    "golang", "go developer", "rust",
    "react native", "dynamics 365", "power apps", "powerbi",
]

EXCLUDE_TITLE_KEYWORDS = [
    # Roles fuera de alcance (seniority / gestión)
    "principal", "staff engineer", "director",
    "head of", "vp of", "cto", "lead",
    "intern", "internship", "práctica", "practica", "practicante", "trainee",
    # Tecnologías / dominios fuera del stack
    "iot",
    # Roles no-dev que contaminan resultados
    "qa", "quality assurance", "automation engineer",
    "designer", "ui/ux", "ux/ui",
    "data analyst", "data engineer", "data science", "data scientist",
    "devops", "sre", "site reliability",
    "salesforce", "apex",
    "support engineer", "technical support",
    "observability", "migration consultant", "upgrade consultant",
    "engineering manager",
    # Tecnologías incompatibles (individual, no frases compuestas)
    "elixir", "golang", "go developer",
    "dynamics 365", "power apps",
    ".net", "c#", "kotlin",
    "ruby", "rails",
    "php", "angular", "drupal",
    "react native",
    "hana",
    "outsystems", "shiny",
    "shopify", "odoo", "moodle",
]

EXCLUDE_COMPANIES = [
    "bairesdev",        # Outsourcing masivo, salarios bajos, no contrata
    "core code io",     # Spam de anuncios genéricos, score siempre 0
    # Ex-empleadores (no volver a postular sin saberlo)
    "klog",
    "depot group",
    "depotgroup",
    "depot chile",
    "grupo mil sabores",
    "grupo los robles",
    "dotsolution",
]


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


def matches_excluded(title: str) -> bool:
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


def matches_excluded_company(company: str) -> bool:
    c = str(company or "").lower()
    return any(excluded in c for excluded in EXCLUDE_COMPANIES)


def has_incompatible_tech(text: str) -> bool:
    text_lower = str(text or "").lower()
    incompatible_count = sum(1 for tech in INCOMPATIBLE_TECH if tech in text_lower)
    return incompatible_count >= 2


def score_job(row) -> int:
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
    if has_incompatible_tech(title):
        score = max(0, score - 5)
    return score


TOTAL_CALLS = (
    len(QUERIES_LINKEDIN_FULL) +
    len(QUERIES_LINKEDIN_LIGHT) * 2 +
    len(QUERIES_INDEED) * 3
)


def _log_call(call_num: int, query: str, country: str, site: str) -> float:
    label = f"[{call_num}/{TOTAL_CALLS}] {query} — {country} ({site})"
    print(f"  {label}...", end="", flush=True)
    return time.time()


def _log_result(t_start: float, count: int) -> None:
    elapsed = time.time() - t_start
    print(f" {count} resultados ({elapsed:.1f}s)")


def scrape_for_country(country: str, country_indeed: str, queries_linkedin: list, call_counter: list) -> list:
    """Scraping separado por sitio para respetar restricciones de cada API."""
    results = []

    # --- LinkedIn: queries específicas por país, con sleep anti-ban ---
    for query in queries_linkedin:
        call_counter[0] += 1
        t = _log_call(call_counter[0], query, country, "LinkedIn")
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
            _log_result(t, len(jobs_linkedin))
        except Exception as e:
            print(f" ERROR: {e}")
        sleep_secs = random.choice([2, 4, 6, 9])
        print(f"    [sleep {sleep_secs}s anti-ban LinkedIn]")
        time.sleep(sleep_secs)

    # --- Indeed: todas las queries (rápido, sin riesgo de ban) ---
    for query in QUERIES_INDEED:
        call_counter[0] += 1
        t = _log_call(call_counter[0], query, country, "Indeed")
        try:
            jobs_indeed = scrape_jobs(
                site_name=SITES_HOURS,
                search_term=query,
                location=country,
                results_wanted=CONFIG["results_wanted"],
                hours_old=CONFIG["hours_old"],
                country_indeed=country_indeed,
                description_format="markdown",
                verbose=0,
            )
            jobs_indeed["search_query"] = query
            jobs_indeed["pais"] = country
            results.append(jobs_indeed)
            _log_result(t, len(jobs_indeed))
        except Exception as e:
            print(f" ERROR: {e}")

    return results


def main() -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    t_start_total = time.time()
    all_jobs = []
    call_counter = [0]  # lista para mutabilidad por referencia

    paises = [
        ("Chile",     "Chile",     QUERIES_LINKEDIN_FULL),
        ("Argentina", "Argentina", QUERIES_LINKEDIN_LIGHT),
        ("Colombia",  "Colombia",  QUERIES_LINKEDIN_LIGHT),
    ]

    for pais_nombre, pais_indeed, queries_linkedin in paises:
        print(f"\n{'='*60}")
        print(f"  Buscando en: {pais_nombre} (LinkedIn: {len(queries_linkedin)}q, Indeed: {len(QUERIES_INDEED)}q)")
        print(f"{'='*60}")
        resultados = scrape_for_country(pais_nombre, pais_indeed, queries_linkedin, call_counter)
        all_jobs.extend(resultados)
        print(f"  → Bloques recolectados de {pais_nombre}: {len(resultados)}")

    if not all_jobs:
        print("\nNo se encontraron trabajos.")
        return

    combined = pd.concat(all_jobs, ignore_index=True)
    print(f"\n[debug] Registros combinados (bruto): {len(combined)}")

    # Dedupe por URL
    before_dedup = len(combined)
    if "job_url" in combined.columns:
        combined = combined.drop_duplicates(subset=["job_url"], keep="first")
    else:
        combined = combined.drop_duplicates()
    print(f"[debug] Tras dedupe: {len(combined)} (descartados: {before_dedup - len(combined)})")

    # Filtro remote: LinkedIn ya viene filtrado con is_remote=True.
    # Indeed puede traer presenciales, filtramos por flag o keywords.
    before_remote = len(combined)
    remote_keywords = ["remote", "remoto", "teletrabajo", "100% remoto", "full remote"]

    def is_likely_remote(row) -> bool:
        if row.get("is_remote") is True:
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
    before_exclude = len(combined)
    mask_title = combined["title"].astype(str).apply(matches_excluded)
    discarded_titles = combined[mask_title]
    combined = combined[~mask_title]
    print(f"[debug] Tras excluir títulos: {len(combined)} (descartados: {len(discarded_titles)})")

    # Excluir empresas
    before_company = len(combined)
    mask_company = combined["company"].astype(str).apply(matches_excluded_company)
    discarded_companies = combined[mask_company]
    combined = combined[~mask_company]
    print(f"[debug] Tras excluir empresas: {len(combined)} (descartados: {len(discarded_companies)})")

    # Score
    combined["match_score"] = combined.apply(score_job, axis=1)

    sort_cols = ["site", "match_score"]
    ascending = [True, False]
    if "date_posted" in combined.columns:
        sort_cols.append("date_posted")
        ascending.append(False)
    combined = combined.sort_values(by=sort_cols, ascending=ascending)

    # Filtro de relevancia
    before_match = len(combined)
    mask_relevance = (
        (combined["match_score"] >= CONFIG["score_minimo"]) |
        (combined["title"].str.contains("fullstack|frontend|backend|developer|ingeniero|desarrollador", case=False, na=False))
    )
    discarded_relevance = combined[~mask_relevance]
    combined = combined[mask_relevance]
    print(f"[debug] Tras filtro relevancia: {len(combined)} (descartados: {len(discarded_relevance)})")

    print(f"\n{'='*80}")
    print(f"TOTAL trabajos relevantes: {len(combined)}")
    print(f"{'='*80}\n")

    columns_to_show = [
        "title", "company", "location", "pais", "date_posted",
        "job_type", "min_amount", "max_amount",
        "job_url", "site", "search_query", "match_score",
    ]
    existing_cols = [c for c in columns_to_show if c in combined.columns]
    print(combined[existing_cols].head(100).to_string(index=False))

    # Crear carpeta del run
    run_dir = Path(__file__).parent / timestamp
    run_dir.mkdir(exist_ok=True)

    # Exportar CSV con metadata de configuración
    out_path = run_dir / "results.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
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
        out_path,
        mode="a",
        quoting=csv.QUOTE_NONNUMERIC,
        escapechar="\\",
        index=False,
    )

    # Exportar resumen legible en Markdown
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

    # Exportar descartados para revisión manual
    discarded_path = run_dir / "discarded.md"
    discard_groups = [
        ("Filtro remote (no parece remoto)", discarded_remote),
        ("Filtro título (keyword excluida)", discarded_titles),
        ("Filtro empresa (empresa excluida)", discarded_companies),
        ("Filtro relevancia (score bajo + título genérico)", discarded_relevance),
    ]
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

    elapsed_total = time.time() - t_start_total
    mins, secs = divmod(int(elapsed_total), 60)
    print(f"\nCarpeta del run: {run_dir}")
    print(f"  → results.csv   (datos completos)")
    print(f"  → results.md    (resumen legible)")
    print(f"  → discarded.md  (descartados para revisión)")
    print(f"Resumen legible en: {md_path}")
    print(f"Tiempo total: {mins}m {secs}s")

    send_email_report(timestamp, md_path, len(df_final))


def send_email_report(run_id: str, results_md_path: Path, total: int) -> None:
    gmail_user = os.environ.get("GMAIL_USER")
    gmail_password = os.environ.get("GMAIL_APP_PASSWORD")
    if not gmail_user or not gmail_password:
        print("[email] Variables GMAIL_USER / GMAIL_APP_PASSWORD no configuradas, saltando.")
        return

    with open(results_md_path) as f:
        body = f.read()

    msg = MIMEMultipart()
    msg["From"] = gmail_user
    msg["To"] = gmail_user
    msg["Subject"] = f"[CRON] job-radar-latam — {total} resultados — {run_id}"
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_password)
            server.send_message(msg)
        print(f"[email] Enviado a {gmail_user}")
    except Exception as e:
        print(f"[email] Error al enviar: {e}")


if __name__ == "__main__":
    main()
