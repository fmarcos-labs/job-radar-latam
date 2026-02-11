import csv
from jobspy import scrape_jobs

SEARCH_QUERIES = [
    "fullstack developer typescript",
    "react next.js developer",
    "flutter developer",
    "node.js nestjs developer",
    "frontend react typescript",
]

SITE_NAMES = ["indeed", "linkedin", "glassdoor", "google", "zip_recruiter"]

all_jobs = []

for query in SEARCH_QUERIES:
    print(f"\n--- Buscando: '{query}' ---")
    try:
        jobs = scrape_jobs(
            site_name=SITE_NAMES,
            search_term=query,
            location="Chile",
            is_remote=True,
            results_wanted=25,
            hours_old=168,  # ultima semana
            country_indeed="Chile",
            description_format="markdown",
            verbose=1,
        )
        print(f"  Encontrados: {len(jobs)} trabajos")
        jobs["search_query"] = query
        all_jobs.append(jobs)
    except Exception as e:
        print(f"  Error en '{query}': {e}")

if all_jobs:
    import pandas as pd

    combined = pd.concat(all_jobs, ignore_index=True)
    combined = combined.drop_duplicates(subset=["job_url"], keep="first")
    combined = combined.sort_values("date_posted", ascending=False)

    print(f"\n{'='*60}")
    print(f"TOTAL trabajos unicos encontrados: {len(combined)}")
    print(f"{'='*60}\n")

    columns_to_show = [
        "title", "company", "location", "date_posted",
        "job_type", "min_amount", "max_amount", "job_url", "search_query",
    ]
    existing_cols = [c for c in columns_to_show if c in combined.columns]
    print(combined[existing_cols].to_string(index=False, max_rows=30))

    combined.to_csv("jobs_results.csv", quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False)
    print(f"\nResultados exportados a: jobs_results.csv")
else:
    print("\nNo se encontraron trabajos.")
