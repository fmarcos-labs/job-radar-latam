import csv
from datetime import datetime
from pathlib import Path

import pandas as pd
from jobspy import scrape_jobs

# Queries optimizadas - enfocadas en tu stack real
SEARCH_QUERIES = [
    # Core stack JavaScript/TypeScript
    "fullstack developer typescript",
    "react developer",
    "nextjs developer",
    "frontend developer typescript",
    "backend developer nodejs",
    "nodejs developer",

    # Core stack Python - REFORZADO
    "python developer",
    "django developer",
    "fastapi developer",
    "backend python developer",
    "django python developer",

    # Mobile - SOLO FLUTTER (sin React Native)
    "flutter developer",
    "flutter mobile developer",
    "mobile developer flutter",

    # Remote LATAM - alta demanda
    "remote developer latam",
    "fullstack remote chile",
    "react remote latam",

    # Seniority levels (incluye todos los niveles)
    "senior fullstack developer",
    "fullstack developer mid level",

    # Especializaciones con demanda real
    "graphql developer",
    "backend developer",
    "frontend developer",

    # AI/Automation - en crecimiento
    "ai engineer",

    # Búsquedas en ESPAÑOL (Chile/LATAM)
    "ingeniero backend",
    "ingeniero fullstack",
    "desarrollador backend",
    "desarrollador fullstack",
    "desarrollador python",
    "desarrollador react",

    # Freelance (empresas pequeñas/startups)
    "freelance developer",
    "fullstack freelance",
    "python freelance developer",
    "desarrollador freelance",
    "freelance react developer",
]

# Sitios soportados por jobspy
SITE_NAMES = ["indeed", "linkedin", "google", "zip_recruiter"]

# Tecnologías principales (peso positivo) - tu stack CORE
CORE_TECH = {
    "typescript": 3,
    "react": 3,
    "next.js": 3,
    "nextjs": 3,
    "node.js": 3,
    "nodejs": 3,
    "nestjs": 3,
    "express": 3,
    "python": 3,
    "django": 3,
    "fastapi": 3,
    "graphql": 2,
    "flutter": 2,
}

# Tecnologías secundarias (peso menor) - complementarias
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
    # "react native" removido - no es tu especialidad (Flutter sí)
}

# Tecnologías incompatibles (penalizan el score)
INCOMPATIBLE_TECH = [
    "elixir",
    "ruby",
    "rails",
    "php",
    "laravel",
    "java",
    "c#",
    ".net",
    "swift",
    "kotlin",
    "golang",
    "go developer",
    "rust",
    "react native",  # No es tu especialidad (Flutter sí)
    "dynamics 365",
    "power apps",
    "powerbi",
]

# Cargos que no te interesen (solo extremos)
EXCLUDE_TITLE_KEYWORDS = [
    "principal engineer",
    "staff engineer",
    "director",
    "head of",
    "vp of",
    "cto",
    "intern",
    "internship",
    "práctica",
    "practicante",
    # Tecnologías incompatibles en títulos
    "elixir",
    "golang",
    "go developer",
    "dynamics 365",
    "power apps",
    ".net developer",
    "c# developer",
    "java developer",
    "react native",  # No es tu especialidad
]

# Empresas excluidas (mala reputación o no contratan)
EXCLUDE_COMPANIES = [
    "bairesdev",
]


def matches_excluded(title: str) -> bool:
    """Excluye roles muy senior/junior o con tecnologías incompatibles"""
    t = (title or "").lower()
    return any(word.lower() in t for word in EXCLUDE_TITLE_KEYWORDS)


def matches_excluded_company(company: str) -> bool:
    """Excluye empresas con mala reputación o que no contratan"""
    c = str(company or "").lower()
    return any(excluded in c for excluded in EXCLUDE_COMPANIES)


def has_incompatible_tech(text: str) -> bool:
    """Detecta si el trabajo requiere tecnologías incompatibles como stack principal"""
    text_lower = str(text or "").lower()
    # Solo penalizamos si aparece en el título (tech principal)
    incompatible_count = sum(1 for tech in INCOMPATIBLE_TECH if tech in text_lower)
    return incompatible_count >= 2  # Si hay 2+ techs incompatibles, probablemente no es tu perfil


def score_job(row) -> int:
    """
    Score positivo basado en match de tecnologías.
    Mayor score = más relevante para tu perfil.
    """
    # Manejo seguro de NaN/None
    title = str(row.get("title", "") or "").lower()
    description = str(row.get("description", "") or "").lower()

    score = 0

    # Bonus por tecnologías core en título (muy importante)
    for tech, weight in CORE_TECH.items():
        if tech in title:
            score += weight * 2  # Doble peso si está en el título
        elif tech in description:
            score += weight

    # Bonus por tecnologías secundarias
    for tech, weight in SECONDARY_TECH.items():
        if tech in title:
            score += weight * 2
        elif tech in description:
            score += weight

    # Penalización por tecnologías incompatibles en título
    if has_incompatible_tech(title):
        score = max(0, score - 5)  # Penaliza pero no elimina completamente

    return score


def main() -> None:
    all_jobs = []

    for query in SEARCH_QUERIES:
        print(f"\n--- Buscando: '{query}' ---")
        try:
            jobs = scrape_jobs(
                site_name=SITE_NAMES,
                search_term=query,
                location="Chile",
                # is_remote=True,  # DESHABILITADO: conflicto con hours_old en Indeed
                results_wanted=50,
                hours_old=168,  # Última semana (prioridad)
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
    print(f"\n[debug] Registros combinados (bruto): {len(combined)}")

    # Filtro inteligente de remote: por flag O por keywords en título/descripción
    before_remote = len(combined)

    # Palabras clave que indican trabajo remoto
    remote_keywords = ["remote", "remoto", "trabajo remoto", "100% remoto", "full remote", "teletrabajo"]

    def is_likely_remote(row) -> bool:
        """Detecta si el trabajo es probablemente remoto"""
        # 1. Si tiene flag is_remote=True, es remoto
        if "is_remote" in row and row.get("is_remote") == True:
            return True

        # 2. Buscar keywords en título y descripción
        # Manejo seguro de NaN/None
        title = str(row.get("title", "") or "").lower()
        description = str(row.get("description", "") or "").lower()
        location = str(row.get("location", "") or "").lower()

        text = f"{title} {description} {location}"
        return any(kw in text for kw in remote_keywords)

    combined = combined[combined.apply(is_likely_remote, axis=1)]
    print(f"[debug] Tras filtro remote: {len(combined)} (descartados: {before_remote - len(combined)})")

    # Eliminar duplicados por URL si existe esa columna
    before_dedup = len(combined)
    if "job_url" in combined.columns:
        combined = combined.drop_duplicates(subset=["job_url"], keep="first")
    else:
        combined = combined.drop_duplicates()
    print(f"[debug] Tras dedupe: {len(combined)} (descartados: {before_dedup - len(combined)})")

    # Excluir títulos que no interesan
    if "title" in combined.columns:
        before_exclude = len(combined)
        mask_exclude = combined["title"].astype(str).apply(matches_excluded)
        combined = combined[~mask_exclude]
        print(f"[debug] Tras excluir títulos: {len(combined)} (descartados: {before_exclude - len(combined)})")

    # Excluir empresas no deseadas (BairesDev, etc.)
    if "company" in combined.columns:
        before_company_exclude = len(combined)
        mask_company_exclude = combined["company"].astype(str).apply(matches_excluded_company)
        combined = combined[~mask_company_exclude]
        print(f"[debug] Tras excluir empresas: {len(combined)} (descartados: {before_company_exclude - len(combined)})")

    # Calcular score de match con tu perfil
    combined["match_score"] = combined.apply(score_job, axis=1)

    # Ordenar por relevancia y por fecha (si existe)
    sort_cols = ["match_score"]
    ascending = [False]
    if "date_posted" in combined.columns:
        sort_cols.append("date_posted")
        ascending.append(False)

    combined = combined.sort_values(by=sort_cols, ascending=ascending)

    # Filtrar trabajos con score muy bajo O con tecnologías incompatibles
    before_match = len(combined)

    # Más inclusivo: mantener trabajos con al menos alguna tecnología relevante
    # O que sean de desarrollo fullstack/frontend/backend genéricos
    combined_filtered = combined[
        (combined["match_score"] >= 2) |  # Al menos 2 puntos de match
        (combined["title"].str.contains("fullstack|frontend|backend|developer", case=False, na=False))
    ]

    descartados = before_match - len(combined_filtered)
    combined = combined_filtered
    print(f"[debug] Tras filtro de relevancia: {len(combined)} (descartados: {descartados})")

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

    # Muestra los 100 más relevantes (más opciones para revisar)
    print(combined[existing_cols].head(100).to_string(index=False))

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
