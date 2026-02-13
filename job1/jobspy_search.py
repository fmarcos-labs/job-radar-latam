import csv
from datetime import datetime
from pathlib import Path

import pandas as pd
from jobspy import scrape_jobs

# Queries pensadas para tu perfil
SEARCH_QUERIES = [
    # Core
    "fullstack developer typescript",
    "react next.js developer",
    "node.js nestjs backend developer",
    "flutter developer",
    "frontend developer react typescript",
    "web scraping puppeteer developer",

    # Batch 1: LATAM remoto / Next.js
    "full stack developer remote latam",
    "fullstack developer 100% remote chile",
    "nextjs developer latam",
    "react developer latam",
    "next.js developer senior",
    "react typescript developer mid-level",
    "nextjs backend developer",

    # Batch 2: Flutter, Python junior, AI/automation
    "flutter clean architecture developer",
    "flutter bloc pattern",
    "flutter bloc developer",
    "flutter remote latam",
    "python developer junior",
    "python backend junior",
    "python junior latam",
    "automation engineer puppeteer",
    "whatsapp business api developer",
    "openai developer",
    "ai engineer javascript",
    "typescript ai automation",
    "strapi graphql developer",
    "supabase developer",
]

# Sitios soportados por jobspy
SITE_NAMES = ["indeed", "linkedin", "google", "zip_recruiter"]

# Palabras clave sacadas de tu CV
KEYWORDS = [
    "typescript",
    "react",
    "next.js",
    "nextjs",
    "node",
    "node.js",
    "nestjs",
    "express",
    "flutter",
    "scraping",
    "puppeteer",
    "graphql",
    "strapi",
    "whatsapp",
    "supabase",
]

# Cargos que no te interesen (ajusta a gusto)
EXCLUDE_TITLE_KEYWORDS = [
    "principal",
    "staff",
    "architect",
    "cto",
    "intern",
    "práctica",
    "practicante",
]


def matches_excluded(title: str) -> bool:
    t = (title or "").lower()
    return any(word.lower() in t for word in EXCLUDE_TITLE_KEYWORDS)


def score_job(row) -> int:
    text = f"{row.get('title', '')} {row.get('description', '')}".lower()
    return sum(1 for kw in KEYWORDS if kw.lower() in text)


def main() -> None:
    all_jobs = []

    for query in SEARCH_QUERIES:
        print(f"\n--- Buscando: '{query}' ---")
        try:
            jobs = scrape_jobs(
                site_name=SITE_NAMES,
                search_term=query,
                location="Chile",
                is_remote=True,
                results_wanted=40,
                hours_old=168,  # última semana
                country_indeed="Chile",
                description_format="markdown",
                verbose=1,
            )
        except Exception as e:
            print(f"  Error en '{query}': {e}")
            continue

        print(f"  Encontrados: {len(jobs)} trabajos")
        jobs["search_query"] = query
        all_jobs.append(jobs)

    if not all_jobs:
        print("\nNo se encontraron trabajos.")
        return

    combined = pd.concat(all_jobs, ignore_index=True)

    # Quedarse solo con trabajos remotos (según flag detectado por JobSpy)
    if "is_remote" in combined.columns:
        combined = combined[combined["is_remote"] == True]

    # Eliminar duplicados por URL si existe esa columna
    if "job_url" in combined.columns:
        combined = combined.drop_duplicates(subset=["job_url"], keep="first")
    else:
        combined = combined.drop_duplicates()

    # Excluir títulos que no interesan
    if "title" in combined.columns:
        mask_exclude = combined["title"].astype(str).apply(matches_excluded)
        combined = combined[~mask_exclude]

    # Calcular score de match con tu perfil
    combined["match_score"] = combined.apply(score_job, axis=1)

    # Ordenar por relevancia y por fecha (si existe)
    sort_cols = ["match_score"]
    ascending = [False]
    if "date_posted" in combined.columns:
        sort_cols.append("date_posted")
        ascending.append(False)

    combined = combined.sort_values(by=sort_cols, ascending=ascending)

    # Quedarse solo con ofertas que al menos matchean 1 keyword
    combined = combined[combined["match_score"] > 0]

    print(f"\n{'=' * 80}")
    print(f"TOTAL trabajos únicos encontrados (relevantes): {len(combined)}")
    print(f"{'=' * 80}\n")

    columns_to_show = [
        "title",
        "company",
        "location",
        "date_posted",
        "job_type",
        "min_amount",
        "max_amount",
        "job_url",
        "site",
        "search_query",
        "match_score",
    ]
    existing_cols = [c for c in columns_to_show if c in combined.columns]

    # Muestra los 40 más relevantes
    print(combined[existing_cols].head(40).to_string(index=False))

    # Guardar con timestamp (para tener histórico)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    out_path = Path(__file__).parent / f"jobs_results_{timestamp}.csv"
    combined.to_csv(
        out_path,
        quoting=csv.QUOTE_NONNUMERIC,
        escapechar="\\",
        index=False,
    )
    print(f"\nResultados exportados a: {out_path}")


if __name__ == "__main__":
    main()
