import csv
import json
import os
from pathlib import Path
import random
import re
import subprocess
import time
import urllib.parse

from urllib.parse import urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup
from jobspy import scrape_jobs
import html as html_mod
import resend

from redirector import leer_clicks

from config import (
    CONFIG,
    QUERIES_INDEED,
    QUERIES_LINKEDIN_FULL,
    QUERIES_LINKEDIN_LIGHT,
    SITES_REMOTE,
    SITES_HOURS,
    CORE_TECH,
    SECONDARY_TECH,
    AI_TECH,
    PLATFORM_TECH,
    INCOMPATIBLE_TECH,
    EXCLUDE_TITLE_KEYWORDS,
    EXCLUDE_COMPANIES,
    LATAM_KEYWORDS,
    TOTAL_CALLS,
    MAX_DESC_FETCH,
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
# Flujo: dedupe → títulos → empresas → memoria → descripción LinkedIn → remote → LATAM → score → relevancia
# Las funciones con _ son helpers internos usados por apply_filters().
# =============================================================================

def _row_mask(df: pd.DataFrame, predicate) -> pd.Series:
    """`df.apply(f, axis=1)` sobre 0 filas devuelve un DataFrame, no una Series, y el `~` revienta."""
    if df.empty:
        return pd.Series(False, index=df.index, dtype=bool)
    return df.apply(predicate, axis=1).astype(bool)


def _row_values(df: pd.DataFrame, fn, dtype):
    if df.empty:
        return pd.Series(dtype=dtype, index=df.index)
    return df.apply(fn, axis=1)

# "home office" es el término más común en Chile/LATAM para trabajo remoto (432 jobs perdidos sin él, run 20260305).
REMOTE_KEYWORDS = [
    "remote", "remoto", "teletrabajo", "full remote",
    "home office", "trabajo remoto", "desde casa", "desde tu casa",
    "trabajo en casa", "100% remoto", "100% remote",
]
NOT_REMOTE_SIGNAL = re.compile(r"h[ií]brid|hybrid|presencial|on-?site|in-office", re.IGNORECASE)
# Frases explícitas de modalidad EN LA DESCRIPCIÓN de LinkedIn (14-11: 73 de 269 "remotos" decían híbrido).
# Deliberadamente no usa NOT_REMOTE_SIGNAL: "hybrid cloud", "apps híbridas" y "no presencial" son de avisos remotos.
DESCRIPTION_NOT_REMOTE_REGEX = re.compile(
    r"modalidad[^.\n]{0,40}(h[ií]brid|presencial)"
    r"|(trabajo|jornada|esquema|modelo|modo|formato)\s+(de trabajo\s+)?h[ií]brid"
    r"|h[ií]brid[oa]\s+(\d|en\b|con\b)"
    r"|\d\s*d[ií]as?\s+(a la semana\s+)?(de forma\s+)?(en (la )?oficina|presencial)"
    r"|asistencia presencial"
    r"|de forma presencial en",
    re.IGNORECASE,
)


def is_likely_remote(row) -> bool:
    """LinkedIn se consulta con is_remote=True (f_WT=2): lo que devuelve es remoto según LinkedIn, y su
    descripción casi nunca repite la palabra (Kraken: 5.658 chars sin "remote"). Solo se descarta si el
    texto dice híbrido/presencial en título/ubicación, o lo dice con una frase explícita de modalidad en la
    descripción (DESCRIPTION_NOT_REMOTE_REGEX). Indeed y Glassdoor no se consultan con ese filtro → keywords."""
    if row.get("site") == "linkedin":
        return not _hybrid_signal(row) and not _description_says_not_remote(row)
    if row.get("site") == "getonbrd":   # la modalidad viene explícita en la tarjeta (Remote / Hybrid / In-office)
        return bool(row.get("is_remote"))
    text = f"{_clean(row.get('title'))} {_clean(row.get('description'))} {_clean(row.get('location'))}".lower()
    return any(kw in text for kw in REMOTE_KEYWORDS)


SEMI_SENIOR_REGEX = re.compile(r"semi[\s-]+(senior|sr\.?)")
# `\bsenior` sin cierre: atrapa "SeniorNode.js" (título pegado). `\bsr\b\.?` atrapa "Sr", "Sr.", "Sr/Dev"
# sin exigir espacio después. III/IV = nivel de escalafón (Software Engineer IV); I y II se conservan.
SENIOR_TITLE_REGEX = re.compile(r"\bsenior|\bsr\b\.?|\b(iii|iv)\b")


def _is_absolute_senior(t: str) -> bool:
    """Excluye 'senior', 'Sr' y niveles III/IV absolutos pero conserva 'semi senior' y 'semi-senior'."""
    if SEMI_SENIOR_REGEX.search(t):
        return False
    return SENIOR_TITLE_REGEX.search(t) is not None


DEV_TITLE_REGEX = re.compile(r"full[\s-]?stack|front[\s-]?end|back[\s-]?end|developer|engineer|ingenier|desarrollador|programador", re.IGNORECASE)


def passes_relevance(row, score_minimo: int) -> bool:
    """Con descripción, manda el score. Sin descripción (LinkedIn sin fetch, tope superado) el título
    de rol dev alcanza: es la única información y perder un buen aviso cuesta más que ver uno malo."""
    if int(row.get("match_score") or 0) >= score_minimo:
        return True
    has_description = bool(str(row.get("description") or "").strip())
    if has_description:
        return False
    return DEV_TITLE_REGEX.search(str(row.get("title") or "")) is not None


def _matches_excluded_title(title: str) -> bool:
    """Retorna True si el título contiene keywords excluidas."""
    t = str(title or "").lower()
    if any(word in t for word in EXCLUDE_TITLE_KEYWORDS):
        return True
    # RECALL: java/go NO se excluyen por titulo — suman 0 al score, un job puro cae por score_minimo
    # y "Node OR Java" sobrevive por Node. Solo queda "cto" (C-Level, seniority) sin atrapar contractor/proyecto.
    if re.search(r"\bcto\b", t):
        return True
    # "intern"/"internship" sin atrapar "International/Internacional"
    if re.search(r"\bintern(ship)?s?\b", t):
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
    for tech, weight in AI_TECH.items():
        if tech in title:
            score += weight * 2
        elif tech in description:
            score += weight
    for tech, weight in PLATFORM_TECH.items():
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
    if row.get("site") == "getonbrd":   # la tarjeta dice en qué países admite residir: eso manda, no una keyword del texto
        return False
    text = (str(row.get("title", "") or "") + " " + str(row.get("description", "") or "")).lower()
    return any(kw in text for kw in LATAM_KEYWORDS)


def _clean(value) -> str:
    """NaN y None son vacío: `str(nan or '')` da 'nan' porque NaN es truthy."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value)


def _job_key(title, company) -> str:
    return f"{_clean(title).strip().lower()}|{_clean(company).strip().lower()}"


def enlace_rastreado(url: str, clave: str) -> str:
    """El link del correo pasa por el redirector (job1/redirector.py) solo si RADAR_CLICK_BASE está puesto
    (`https://radar.fmarcos.dev/r/<token>`); sin la variable, la URL real, como siempre."""
    base = os.environ.get("RADAR_CLICK_BASE", "").strip()
    if not base or not url:
        return url
    return f"{base}?{urllib.parse.urlencode({'k': clave, 'u': url})}"


def marcar_abiertos(combined: pd.DataFrame, clicks_file) -> pd.DataFrame:
    """Columna `abierto`: hora de la primera apertura según clicks.json (misma clave que la memoria), o vacío."""
    out = combined.copy()
    clicks = leer_clicks(clicks_file)
    out["abierto"] = [clicks.get(_job_key(r.get("title"), r.get("company")), "") for _, r in out.iterrows()] if len(out) else []
    return out


def _description_says_not_remote(row) -> bool:
    return DESCRIPTION_NOT_REMOTE_REGEX.search(_clean(row.get("description"))) is not None


def _hybrid_signal(row) -> bool:
    """Señal de no-remoto en título + ubicación (NO palabras sueltas de la descripción: 'hybrid cloud', 'no presencial'
    y 'apps híbridas' aparecen en avisos remotos; medido: la señal real estaba en 11 títulos de 608).
    Las frases explícitas de modalidad en la descripción se miran aparte: `_description_says_not_remote`."""
    return NOT_REMOTE_SIGNAL.search(f"{_clean(row.get('title'))} {_clean(row.get('location'))}") is not None


# =============================================================================
# DESCRIPCIÓN DE LINKEDIN (solo para avisos nuevos)
#
# JobSpy 1.1.82 solo baja la descripción de LinkedIn con `linkedin_fetch_description=True` (1 request
# por job, para TODOS los resultados). Acá se baja solo para los nuevos: mismo endpoint y selector que
# JobSpy (`jobspy/linkedin/__init__.py::_get_job_details`), headers propios para no depender de sus internos.
# =============================================================================

LINKEDIN_JOB_VIEW = "https://www.linkedin.com/jobs/view/{job_id}"
LINKEDIN_HEADERS = {
    "authority": "www.linkedin.com",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "max-age=0",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}
DESC_SLEEP_RANGE = (2, 4)   # segundos entre requests a LinkedIn (soft-ban)
MAX_CONSECUTIVE_FETCH_FAILURES = 5   # 5 seguidas = LinkedIn nos bloqueó: no insistir 145 veces más


def parse_linkedin_description(html: str):
    """Texto plano del bloque de descripción de la página pública del job; None si no está."""
    soup = BeautifulSoup(html, "html.parser")
    block = soup.find("div", class_=lambda c: c and "show-more-less-html__markup" in c)
    if block is None:
        return None
    text = block.get_text(" ", strip=True)
    return text or None


def _linkedin_job_id(url) -> str | None:
    match = re.search(r"/jobs/view/(\d+)", str(url or ""))
    return match.group(1) if match else None


def _http_get_linkedin_job(job_id: str) -> str:
    response = requests.get(LINKEDIN_JOB_VIEW.format(job_id=job_id), headers=LINKEDIN_HEADERS, timeout=10)
    # raise_for_status no ve el 999 de LinkedIn (no es 4xx/5xx); y un redirect a /authwall o /signup es bloqueo
    if response.status_code != 200:
        raise RuntimeError(f"LinkedIn respondió {response.status_code}")
    if not urlparse(response.url).path.startswith("/jobs/view/"):
        raise RuntimeError(f"LinkedIn redirigió a {response.url[:60]}")
    return response.text


def fetch_linkedin_descriptions(jobs: pd.DataFrame, fetch=_http_get_linkedin_job, max_fetch: int = 150, sleep=None) -> pd.DataFrame:
    """Completa `description` SOLO en filas de LinkedIn sin texto, hasta `max_fetch`, con pausa entre
    requests. Una falla no corta la corrida: la fila queda sin texto y `desc_fetched=False`."""
    pause = sleep or (lambda: time.sleep(random.uniform(*DESC_SLEEP_RANGE)))
    out = jobs.copy()
    if "description" not in out.columns:
        out["description"] = ""
    out["desc_fetched"] = False
    fetched = 0
    consecutive_failures = 0
    for idx, row in out.iterrows():
        if row.get("site") != "linkedin" or _clean(row.get("description")).strip():
            continue
        if fetched >= max_fetch:
            break
        if consecutive_failures >= MAX_CONSECUTIVE_FETCH_FAILURES:
            print(f"  [desc] {consecutive_failures} fallas seguidas: LinkedIn bloqueó, se corta el fetch de esta corrida")
            break
        job_id = _linkedin_job_id(row.get("job_url"))
        if not job_id:
            continue
        fetched += 1
        try:
            text = parse_linkedin_description(fetch(job_id))
        except Exception as error:
            consecutive_failures += 1
            print(f"  [desc] {job_id}: {error}")
            pause()
            continue
        consecutive_failures = 0
        if text:
            out.at[idx, "description"] = text
            out.at[idx, "desc_fetched"] = True
        pause()
    return out


class SeenStore:
    """Memoria entre corridas, persistida fuera del rsync del deploy. Clave: título|empresa normalizados.
    Dos marcas por aviso: EVALUADO (`first_run`, con su descripción, para no volver a pedirla ni dejarlo
    entrar vacío por el bypass) y MOSTRADO (`shown_run`, lo que define qué es NUEVO en el email).
    Medido: sin esto el 75-87 % de cada email era repetido."""

    def __init__(self, path, today: str | None = None, max_age_days: int = 30):
        self.path = Path(path)
        self.data = self._load()
        self._expire(today or time.strftime("%Y%m%d_%H%M"), max_age_days)

    def _load(self) -> dict:
        """Un archivo truncado (apagón a mitad de escritura) no puede tumbar todas las corridas siguientes:
        se aparta con fecha y se arranca vacío (costo: una corrida con todo como NUEVO)."""
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            aside = self.path.with_name(f"{self.path.name}.corrupt-{time.strftime('%Y%m%d_%H%M%S')}")
            self.path.rename(aside)
            print(f"[seen] archivo corrupto ({error}); apartado en {aside.name}, se arranca vacío")
            return {}

    def _expire(self, today: str, max_age_days: int) -> None:
        """Un aviso republicado meses después vuelve a ser NUEVO, y el archivo no crece para siempre."""
        cutoff = time.strftime("%Y%m%d", time.localtime(time.mktime(time.strptime(today[:8], "%Y%m%d")) - max_age_days * 86400))

        def expired(entry) -> bool:
            stamp = str(entry.get("first_run", ""))[:8]
            return len(stamp) == 8 and stamp.isdigit() and stamp < cutoff   # sin fecha legible no se vence

        self.data = {k: v for k, v in self.data.items() if not expired(v)}

    @staticmethod
    def _keys(jobs: pd.DataFrame) -> pd.Series:
        return jobs.apply(lambda r: _job_key(r.get("title"), r.get("company")), axis=1)

    def split_new(self, jobs: pd.DataFrame) -> tuple:
        """(nunca_evaluados, ya_evaluados) manteniendo el DataFrame original."""
        if jobs.empty:
            return jobs, jobs
        is_new = ~self._keys(jobs).isin(self.data.keys())
        return jobs[is_new], jobs[~is_new]

    def was_shown(self, jobs: pd.DataFrame) -> pd.Series:
        if jobs.empty:
            return pd.Series(False, index=jobs.index, dtype=bool)
        return self._keys(jobs).map(lambda k: "shown_run" in self.data.get(k, {})).astype(bool)

    def fill_descriptions(self, jobs: pd.DataFrame) -> pd.DataFrame:
        """Completa `description` vacía con la guardada en una corrida anterior (0 requests)."""
        out = jobs.copy()
        if out.empty:
            return out
        for idx, key in self._keys(out).items():
            stored = self.data.get(key, {}).get("description")
            if stored and not _clean(out.at[idx, "description"]).strip():
                out.at[idx, "description"] = stored
        return out

    def remember(self, jobs: pd.DataFrame, run_id: str) -> None:
        """Registra lo EVALUADO en esta corrida (first_run nunca se pisa) y guarda su descripción si la trae."""
        for _, row in jobs.iterrows():
            entry = self.data.setdefault(_job_key(row.get("title"), row.get("company")), {"first_run": run_id})
            text = _clean(row.get("description")).strip()
            # Solo LinkedIn: Indeed/Glassdoor traen la descripción en cada corrida, guardarla solo engorda el archivo
            if text and row.get("site") == "linkedin" and not entry.get("description"):
                entry["description"] = text
        self._save()

    def mark_shown(self, jobs: pd.DataFrame, run_id: str) -> None:
        """Registra lo MOSTRADO (lo que fue al email); se llama después de enviarlo."""
        for _, row in jobs.iterrows():
            entry = self.data.setdefault(_job_key(row.get("title"), row.get("company")), {"first_run": run_id})
            entry.setdefault("shown_run", run_id)
        self._save()

    def _save(self) -> None:
        """Atómico: tmp + os.replace. Un proceso que muere a mitad de escritura no deja un JSON truncado."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(self.data, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self.path)


def dedupe_jobs(combined: pd.DataFrame) -> pd.DataFrame:
    """El mismo aviso publicado con varias URLs (por región, por re-posteo) es UNA fila.
    Clave: título + empresa normalizados. Con match_score presente se conserva la fila de mayor score.
    Medido 20261103_1030: 53 filas → 31 avisos reales."""
    if combined.empty:
        return combined
    keyed = combined.assign(
        _job_key=combined.apply(lambda r: _job_key(r.get("title"), r.get("company")), axis=1),
        _hybrid=combined.apply(_hybrid_signal, axis=1),
    )
    # Entre gemelos gana el que no dice híbrido (si no, el dedupe se queda con el presencial y el remoto se pierde)
    sort_cols, asc = ["_hybrid"], [True]
    if "match_score" in keyed.columns:
        sort_cols, asc = ["_hybrid", "match_score"], [True, False]
    keyed = keyed.sort_values(sort_cols, ascending=asc, kind="stable")
    return keyed.drop_duplicates(subset=["_job_key"], keep="first").drop(columns=["_job_key", "_hybrid"]).sort_index()


def apply_filters(combined: pd.DataFrame, seen_store=None, fetch=_http_get_linkedin_job,
                  max_desc_fetch: int = MAX_DESC_FETCH, sleep=None, run_id: str = "") -> tuple:
    """Aplica todos los filtros en orden. Retorna (combined_filtrado, discard_groups).

    Orden: dedupe URL → dedupe título+empresa → excluir títulos/empresas → vistos (is_new) →
    descripción SOLO para LinkedIn nuevos → remoto → LATAM → score → relevancia.
    Las exclusiones por título/empresa van ANTES del fetch: no se gasta un request en lo que se descarta igual.
    """

    # Dedupe por URL y por título+empresa (el mismo aviso con 3 URLs era 3 filas)
    before_dedup = len(combined)
    if "job_url" in combined.columns:
        combined = combined.drop_duplicates(subset=["job_url"], keep="first")
    else:
        combined = combined.drop_duplicates()
    combined = dedupe_jobs(combined)
    print(f"[debug] Tras dedupe: {len(combined)} (descartados: {before_dedup - len(combined)})")

    # Excluir títulos incompatibles
    # (.astype(bool): con 0 filas la Series vacía queda object y pandas la lee como lista de columnas → df sin columnas)
    mask_title = combined["title"].astype(str).apply(_matches_excluded_title).astype(bool)
    discarded_titles = combined[mask_title]
    combined = combined[~mask_title]
    print(f"[debug] Tras excluir títulos: {len(combined)} (descartados: {len(discarded_titles)})")

    # Excluir empresas
    mask_company = combined["company"].astype(str).apply(_matches_excluded_company).astype(bool)
    discarded_companies = combined[mask_company]
    combined = combined[~mask_company].copy()
    print(f"[debug] Tras excluir empresas: {len(combined)} (descartados: {len(discarded_companies)})")

    # Memoria: NUEVO = nunca mostrado; lo ya evaluado reusa su descripción y no gasta requests
    if "description" not in combined.columns:
        combined["description"] = ""
    combined["description"] = combined["description"].fillna("")
    if seen_store is not None:
        never_evaluated, _ = seen_store.split_new(combined)
        combined["is_new"] = ~seen_store.was_shown(combined)
        combined = seen_store.fill_descriptions(combined)
    else:
        never_evaluated = combined
        combined["is_new"] = True
    # Candidatos: LinkedIn SIN texto (lo que el tope o un 429 dejó afuera se reintenta), nunca evaluados primero
    sin_texto = combined[(combined["site"] == "linkedin") & (combined["description"].str.strip() == "")]
    to_fetch = pd.concat([sin_texto[sin_texto.index.isin(never_evaluated.index)], sin_texto[~sin_texto.index.isin(never_evaluated.index)]])
    print(f"[debug] Nuevos (nunca mostrados): {int(combined['is_new'].sum())} · LinkedIn sin descripción: {len(to_fetch)}")

    # Descripción de LinkedIn solo para lo que no tiene texto (tope + sleep; Indeed/Glassdoor ya la traen)
    combined["desc_fetched"] = False
    fetched = fetch_linkedin_descriptions(to_fetch, fetch=fetch, max_fetch=max_desc_fetch, sleep=sleep)
    combined.loc[fetched.index, "description"] = fetched["description"]
    combined.loc[fetched.index, "desc_fetched"] = fetched["desc_fetched"]
    print(f"[debug] Descripciones de LinkedIn bajadas: {int(fetched['desc_fetched'].sum())} (tope {max_desc_fetch})")
    if seen_store is not None:
        seen_store.remember(combined, run_id=run_id)   # ya evaluado, con texto: aunque la corrida muera después

    # Filtro remote: LinkedIn confía en su búsqueda (f_WT=2); Indeed/Glassdoor por keywords. Ver is_likely_remote.
    mask_remote = _row_mask(combined, is_likely_remote)
    discarded_remote = combined[~mask_remote]
    combined = combined[mask_remote]
    print(f"[debug] Tras filtro remote: {len(combined)} (descartados: {len(discarded_remote)})")

    # Filtro LATAM: jobs no-chilenos solo pasan si mencionan apertura regional
    mask_latam = _row_mask(combined, _is_latam_open)
    discarded_latam = combined[~mask_latam]
    combined = combined[mask_latam]
    print(f"[debug] Tras filtro LATAM: {len(combined)} (descartados: {len(discarded_latam)})")

    # Score
    combined = combined.copy()
    combined["match_score"] = _row_values(combined, _calculate_match_score, dtype=int)

    sort_cols = ["site", "match_score"]
    ascending = [True, False]
    if "date_posted" in combined.columns:
        sort_cols.append("date_posted")
        ascending.append(False)
    combined = combined.sort_values(by=sort_cols, ascending=ascending)

    # Filtro de relevancia
    mask_relevance = _row_mask(combined, lambda r: passes_relevance(r, CONFIG["score_minimo"]))
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

def export_results(combined: pd.DataFrame, discard_groups: list, run_dir: Path, timestamp: str,
                   version: str = CONFIG["version"], sha: str = "sin-sha") -> Path:
    """Exporta los 3 archivos del run: results.csv, results.md, discarded.md.
    results.md abre con los NUEVOS (columna is_new) ordenados por score; sin la columna, todo es nuevo.
    Retorna la ruta al archivo results.md (usado para el email).
    """
    is_new = combined["is_new"].astype(bool) if "is_new" in combined.columns else pd.Series(True, index=combined.index)
    nuevos = combined[is_new].sort_values("match_score", ascending=False) if "match_score" in combined.columns else combined[is_new]
    vistos = int((~is_new).sum())

    # --- results.csv (datos completos con metadata de configuración) ---
    csv_path = run_dir / "results.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        f.write(f"# CONFIG_VERSION={version}\n")
        f.write(f"# GIT_SHA={sha}\n")
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
        f.write(f"**Total:** {len(combined)} trabajos | **Nuevos:** {len(nuevos)}")
        f.write(f" | **Score minimo:** {CONFIG['score_minimo']}")
        f.write(f" | **Paises:** {', '.join(CONFIG['paises'])}")
        f.write(f" | **Version:** {version} ({sha})\n\n")
        f.write("---\n\n")
        f.write(f"## NUEVOS ({len(nuevos)})\n\n")
        f.write("| Score | Titulo | Empresa | Pais | Sitio | Fecha |\n")
        f.write("|------:|--------|---------|------|-------|-------|\n")
        for _, row in nuevos.iterrows():
            url = str(row.get("job_url", "") or "")
            title_cell = f"[{row.get('title', '')}]({url})" if url else str(row.get("title", ""))
            f.write(f"| {int(row.get('match_score', 0) or 0)} | {title_cell} | {row.get('company', '')} | {row.get('pais', '')} | {row.get('site', '')} | {row.get('date_posted', '')} |\n")
        f.write(f"\n(ya vistos en corridas anteriores: {vistos})\n\n---\n\n")
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

    # --- results.html (cuerpo HTML del email: NUEVOS con el score pesado) ---
    (run_dir / "results.html").write_text(render_results_html(combined, timestamp, version, sha), encoding="utf-8")

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
# CORREO HTML — el score pesa visualmente; ninguna fila se oculta, nada ocupa espacio de más
# =============================================================================

def _tier(score: int, fuerte: int, medio: int) -> str:
    if score >= fuerte:
        return "fuerte"
    if score >= medio:
        return "medio"
    return "flojo"


def fecha_visible(row) -> str:
    """La fecha como se muestra: GetOnBoard no trae el año en la tarjeta (Sonda de mayo-2025 salía como 2026),
    así que la suya va sin año («20-may»); las demás, tal cual."""
    fecha = row.get("date_posted")
    if fecha is None or (isinstance(fecha, float) and pd.isna(fecha)):
        return ""
    if row.get("site") == "getonbrd":
        try:
            return pd.Timestamp(fecha).strftime("%d-%b").lower()
        except (ValueError, TypeError):
            return str(fecha)
    return str(fecha)


def _celda(valor) -> str:
    """Texto de una celda: NaN/None es vacío, nunca «nan»."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return ""
    return html_mod.escape(str(valor))


def render_results_html(combined: pd.DataFrame, timestamp: str, version: str, sha: str,
                        fuerte: int = None, medio: int = None) -> str:
    """Solo los NUEVOS, por score: fila densa (13px, sin botones), el score en negrita y color
    según tier, el título en negrita si es fuerte y gris si es flojo. Un 0 sin descripción se
    marca «s/d»: no es mal match, es que LinkedIn no dio el texto."""
    fuerte = CONFIG["score_fuerte"] if fuerte is None else fuerte
    medio = CONFIG["score_medio"] if medio is None else medio
    is_new = combined["is_new"].astype(bool) if "is_new" in combined.columns else pd.Series(True, index=combined.index)
    nuevos = combined[is_new].sort_values("match_score", ascending=False) if "match_score" in combined.columns else combined[is_new]
    vistos = int((~is_new).sum())
    color = {"fuerte": "#1a7f37", "medio": "#1f2328", "flojo": "#8b949e"}
    filas = []
    for _, row in nuevos.iterrows():
        score = int(row.get("match_score", 0) or 0)
        tier = _tier(score, fuerte, medio)
        sin_texto = score == 0 and not str(row.get("description", "") or "").strip()
        url = str(row.get("job_url", "") or "")
        titulo = html_mod.escape(str(row.get("title", "") or ""))
        titulo = f"<b>{titulo}</b>" if tier == "fuerte" else titulo
        href = enlace_rastreado(url, _job_key(row.get("title"), row.get("company")))
        enlace = f'<a href="{html_mod.escape(href)}" style="color:{color[tier]};text-decoration:none">{titulo}</a>' if url else titulo
        score_txt = f"{score}&nbsp;<span style=\"font-weight:normal;font-size:11px\">s/d</span>" if sin_texto else str(score)
        peso = "font-weight:700;font-size:15px" if tier == "fuerte" else ("font-weight:600" if tier == "medio" else "font-weight:400")
        filas.append(
            f'<tr class="fila {tier}" style="color:{color[tier]}">'
            f'<td style="text-align:right;padding:1px 6px;{peso}">{score_txt}</td>'
            f'<td style="padding:1px 6px">{enlace}</td>'
            f'<td style="padding:1px 6px">{_celda(row.get("company"))}</td>'
            f'<td style="padding:1px 6px">{_celda(row.get("pais"))}</td>'
            f'<td style="padding:1px 6px">{_celda(row.get("site"))}</td>'
            f'<td style="padding:1px 6px;white-space:nowrap">{_celda(fecha_visible(row))}</td>'
            "</tr>"
        )
    cabecera = (
        f'<p style="margin:0 0 6px 0"><b>NUEVOS ({len(nuevos)})</b> · ya vistos: {vistos} · '
        f'score ≥{fuerte} fuerte · ≥{medio} medio · s/d = sin descripción · {html_mod.escape(version)} ({html_mod.escape(sha)}) · {timestamp}</p>'
    )
    tabla = (
        '<table style="border-collapse:collapse;font:13px/1.35 -apple-system,Segoe UI,Roboto,sans-serif;width:100%">'
        '<thead><tr style="color:#57606a;font-size:11px"><th style="text-align:right;padding:1px 6px">score</th>'
        '<th style="text-align:left;padding:1px 6px">título</th><th style="text-align:left;padding:1px 6px">empresa</th>'
        '<th style="text-align:left;padding:1px 6px">país</th><th style="text-align:left;padding:1px 6px">sitio</th>'
        '<th style="text-align:left;padding:1px 6px">fecha</th></tr></thead><tbody>\n'
        + "\n".join(filas) + "\n</tbody></table>"
    )
    return f'<!doctype html><html><body style="margin:8px;color:#1f2328">{cabecera}{tabla}</body></html>\n'

# =============================================================================
# EMAIL
# =============================================================================

def build_email_subject(new_count: int, total: int, version: str, sha: str, run_id: str) -> str:
    """Nuevos primero, y la iteración (versión + commit) a la vista: dos emails de épocas distintas se
    distinguen sin abrir el repo."""
    return f"⭐ Job Radar LATAM — {new_count} nuevos / {total} — {version} ({sha}) — {run_id}"


def read_git_sha(app_dir) -> str:
    """El deploy escribe GIT_SHA junto al código; sin archivo se intenta `git rev-parse` (el rsync copia .git);
    sin ninguno queda explícito."""
    sha_file = Path(app_dir) / "GIT_SHA"
    if sha_file.exists():
        return sha_file.read_text(encoding="utf-8").strip() or "sin-sha"
    try:
        out = subprocess.run(["git", "-C", str(app_dir), "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=5)
        return out.stdout.strip() if out.returncode == 0 and out.stdout.strip() else "sin-sha"
    except Exception:
        return "sin-sha"


def send_email_report(run_id: str, results_md_path: Path, total: int, new_count: int = 0,
                      version: str = CONFIG["version"], sha: str = "sin-sha") -> bool:
    """True solo si el email salió: de eso depende marcar los avisos como mostrados."""
    api_key = os.environ.get("RESEND_API_KEY")
    to_email = os.environ.get("RESEND_TO_EMAIL")
    if not api_key or not to_email:
        print("[email] Variables RESEND_API_KEY / RESEND_TO_EMAIL no configuradas, saltando.")
        return False

    with open(results_md_path) as f:
        body = f.read()
    html_path = results_md_path.with_name("results.html")
    html_body = html_path.read_text(encoding="utf-8") if html_path.exists() else None

    resend.api_key = api_key

    try:
        resend.Emails.send({
            "from": "job-radar@resend.dev",
            "to": to_email,
            "subject": build_email_subject(new_count, total, version, sha, run_id),
            "text": body,
            **({"html": html_body} if html_body else {}),
            "headers": {
                "X-Priority": "1",
                "Importance": "high",
            },
        })
        print(f"[email] Enviado a {to_email}")
        return True
    except Exception as e:
        print(f"[email] Error al enviar: {e}")
        return False
