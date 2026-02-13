from __future__ import annotations

import csv
import subprocess
from datetime import datetime
from pathlib import Path

import pandas as pd


def main() -> None:
    base_dir = Path(__file__).parent
    settings_path = base_dir / "jobfunnel_settings.yaml"
    output_dir = base_dir / "job2_results"
    master_csv = output_dir / "master_list.csv"

    print(f"Usando configuración JobFunnel: {settings_path}")
    # Ejecutamos el CLI oficial de JobFunnel (`funnel`)
    result = subprocess.run(
        ["funnel", "load", "-s", str(settings_path)],
        cwd=base_dir,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print("\n⚠️  JobFunnel falló al hacer scraping.")
        print("Esto suele pasar porque las webs (Indeed/Monster) cambian el HTML")
        print("y la versión instalada de JobFunnel no las reconoce.\n")
        print(f"Código de salida: {result.returncode}")
        if result.stderr:
            print("Detalle técnico (resumen de JobFunnel):")
            print(result.stderr.strip().splitlines()[-1])
        print("\nTu configuración y tu script están bien; es un problema del scraper.")
        print("Mientras tanto, usa `job1` que no depende de JobFunnel.")
        return

    if not master_csv.exists():
        print("\nJobFunnel terminó pero no se encontró el CSV maestro.")
        print(f"Buscado en: {master_csv}")
        return

    # Leer resultados de JobFunnel
    df = pd.read_csv(master_csv)

    if df.empty:
        print("\nJobFunnel terminó pero no encontró trabajos.")
        return

    # Filtrar solo los que sigan “activos” (status vacío o 'new')
    if "status" in df.columns:
        df = df[df["status"].isna() | df["status"].isin(["new", "interested"])]

    # Ordenar por fecha de publicación si existe esa columna
    for date_col in ["date_added", "date_last_seen", "date_posted"]:
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            df = df.sort_values(by=[date_col], ascending=False)
            break

    # Mostrar columnas principales similares a job1
    columns_preferidas = [
        "title",
        "company",
        "location",
        "date_posted",
        "date_added",
        "url",
        "job_board",
    ]
    cols_existentes = [c for c in columns_preferidas if c in df.columns]

    print("\n" + "=" * 80)
    print(f"TOTAL trabajos únicos encontrados (JobFunnel): {len(df)}")
    print("=" * 80 + "\n")

    if cols_existentes:
        print(df[cols_existentes].head(40).to_string(index=False))
    else:
        print(df.head(40).to_string(index=False))

    # Exportar a un CSV con timestamp (como job1)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    out_path = output_dir / f"jobfunnel_results_{timestamp}.csv"
    df.to_csv(
        out_path,
        quoting=csv.QUOTE_NONNUMERIC,
        escapechar="\\",
        index=False,
    )

    print(f"\nResultados exportados a: {out_path}")


if __name__ == "__main__":
    main()
