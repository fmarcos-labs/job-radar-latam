from datetime import datetime
from pathlib import Path
import time

import pandas as pd

from config import CLICKS_FILE, CONFIG, MAX_DESC_FETCH, SEEN_FILENAME
from getonbrd import scrape_getonbrd
from helpers import (
    marcar_abiertos,
    SeenStore,
    apply_filters,
    export_results,
    read_git_sha,
    scrape_all_countries,
    send_alert_email,
    send_email_report,
    should_send_report,
)
from salud import evaluar_salud

JOB_DIR = Path(__file__).parent   # carpetas de corrida y memoria


def main() -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    t_start_total = time.time()

    # 0. Memoria y sha ANTES de scrapear: si fallan, que fallen a los 0 min y no a los 17
    app_dir = Path(__file__).parent.parent
    sha = read_git_sha(app_dir)
    seen = SeenStore(JOB_DIR / SEEN_FILENAME)

    # 1. Scraping — LinkedIn + Indeed × 3 países
    all_jobs = scrape_all_countries()
    # GetOnBoard: el portal tech chileno, por su HTML público; misma forma que JobSpy, mismos filtros
    getonbrd_jobs = scrape_getonbrd()
    if len(getonbrd_jobs):
        all_jobs.append(getonbrd_jobs)

    # Salud ANTES de filtrar: filas crudas por fuente y horas desde la última corrida con datos
    salud = evaluar_salud(all_jobs, JOB_DIR, timestamp)
    if salud.sin_datos:
        print(f"\nNo se encontraron trabajos: {'; '.join(salud.avisos)}")
        send_alert_email(timestamp, salud, version=CONFIG["version"], sha=sha)
        return

    combined = pd.concat(all_jobs, ignore_index=True)
    print(f"\n[debug] Registros combinados (bruto): {len(combined)}")

    # 2. Pipeline de filtros — dedupe, títulos, empresas, memoria, descripción (LinkedIn sin texto), remoto, LATAM, score, relevancia
    combined, discard_groups = apply_filters(combined, seen_store=seen, max_desc_fetch=MAX_DESC_FETCH, run_id=timestamp)
    combined = marcar_abiertos(combined, CLICKS_FILE)   # qué se abrió desde correos anteriores (job1/redirector.py)
    new_count = int(combined["is_new"].sum())

    print(f"\n{'='*80}")
    print(f"TOTAL trabajos relevantes: {len(combined)} · NUEVOS: {new_count} · {CONFIG['version']} ({sha})")
    print(f"{'='*80}\n")

    # 3. Preview en consola
    columns_to_show = [
        "title", "company", "location", "pais", "date_posted",
        "job_type", "min_amount", "max_amount",
        "job_url", "site", "search_query", "match_score", "is_new", "desc_fetched",
    ]
    existing_cols = [c for c in columns_to_show if c in combined.columns]
    print(combined[existing_cols].head(100).to_string(index=False))

    # 4. Exportar resultados — CSV, Markdown, descartados
    run_dir = JOB_DIR / timestamp
    run_dir.mkdir(exist_ok=True)

    results_md_path = export_results(combined, discard_groups, run_dir, timestamp, version=CONFIG["version"], sha=sha, salud=salud)

    elapsed_total = time.time() - t_start_total
    mins, secs = divmod(int(elapsed_total), 60)
    print(f"\nCarpeta del run: {run_dir}")
    print(f"  → results.csv   (datos completos)")
    print(f"  → results.md    (resumen legible)")
    print(f"  → discarded.md  (descartados para revisión)")
    print(f"Resumen legible en: {results_md_path}")
    print(f"Tiempo total: {mins}m {secs}s")

    # 5. Email con results.md (NUEVOS arriba). Con 0 nuevas y sin aviso de salud no se envía: la corrida queda en el log.
    #    Solo si SALIÓ se marcan como mostrados: si el email falla, la corrida siguiente los vuelve a mostrar
    #    como NUEVOS (sin re-pedir descripciones: ya están en la memoria).
    if not should_send_report(new_count, salud):
        print(f"[email] 0 nuevas: no se envía correo (corrida {timestamp}, {len(combined)} relevantes ya vistos)")
        return
    sent = send_email_report(timestamp, results_md_path, len(combined), new_count=new_count, version=CONFIG["version"], sha=sha, salud=salud)
    if sent:
        seen.mark_shown(combined, run_id=timestamp)
    else:
        print("[seen] email no enviado: nada se marca como mostrado")


if __name__ == "__main__":
    main()
