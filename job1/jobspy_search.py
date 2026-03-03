from datetime import datetime
from pathlib import Path
import time

import pandas as pd

from helpers import (
    scrape_all_countries,
    apply_filters,
    export_csv,
    export_markdown,
    export_discarded,
    send_email_report,
)


def main() -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    t_start_total = time.time()

    # 1. Scraping — LinkedIn + Indeed × 3 países
    all_jobs = scrape_all_countries()

    if not all_jobs:
        print("\nNo se encontraron trabajos.")
        return

    combined = pd.concat(all_jobs, ignore_index=True)
    print(f"\n[debug] Registros combinados (bruto): {len(combined)}")

    # 2. Pipeline de filtros — dedupe, remote, títulos, empresas, score, relevancia
    combined, discard_groups = apply_filters(combined)

    print(f"\n{'='*80}")
    print(f"TOTAL trabajos relevantes: {len(combined)}")
    print(f"{'='*80}\n")

    # 3. Preview en consola
    columns_to_show = [
        "title", "company", "location", "pais", "date_posted",
        "job_type", "min_amount", "max_amount",
        "job_url", "site", "search_query", "match_score",
    ]
    existing_cols = [c for c in columns_to_show if c in combined.columns]
    print(combined[existing_cols].head(100).to_string(index=False))

    # 4. Exportar resultados — CSV, Markdown, descartados
    run_dir = Path(__file__).parent / timestamp
    run_dir.mkdir(exist_ok=True)

    export_csv(combined, run_dir, timestamp)
    md_path = export_markdown(combined, run_dir, timestamp)
    export_discarded(discard_groups, run_dir, timestamp)

    elapsed_total = time.time() - t_start_total
    mins, secs = divmod(int(elapsed_total), 60)
    print(f"\nCarpeta del run: {run_dir}")
    print(f"  → results.csv   (datos completos)")
    print(f"  → results.md    (resumen legible)")
    print(f"  → discarded.md  (descartados para revisión)")
    print(f"Resumen legible en: {md_path}")
    print(f"Tiempo total: {mins}m {secs}s")

    # 5. Email con resultados
    send_email_report(timestamp, md_path, len(combined))


if __name__ == "__main__":
    main()
