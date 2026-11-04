"""GetOnBoard (getonbrd.com), el portal tech chileno, como fuente del radar.

No tiene API pública (api/v2 da 404), pero el listado se lee sin login y cada tarjeta trae todo lo
que el pipeline necesita: título, empresa, modalidad, lugar, en qué países admite residir (remotos),
sueldo, fecha y un resumen del aviso. Por eso NO se baja la página de cada aviso: dos requests por
corrida y ningún riesgo de bloqueo.

Medido el 2026-11-03 (fixtures en tests/fixtures/getonbrd/): `?countries=CL` no filtra nada (313
avisos con y sin él, idénticos): el listado es global y el país sale de la tarjeta. 362 avisos
únicos; el más viejo tenía 354 días, así que «Nov 03» sin año es inequívoco dentro de los últimos
365 días (si GetOnBoard dejara un aviso más de un año, se leería como reciente).
"""
import random
import re
import time
from datetime import date

import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE = "https://www.getonbrd.com"
CATEGORIES = ("programacion", "machine-learning-ai")
HEADERS = {"user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
           "accept-language": "es-CL,es;q=0.9,en;q=0.8"}
TIMEOUT = 20
LISTING_SLEEP = (2, 4)
# «Admite Chile»: lo nombra, o admite la región, o el mundo. `pais="Chile"` significa lo mismo que en
# JobSpy: el aviso aplica para Chile, no que la empresa esté acá.
ADMITE_CHILE = re.compile(r"chile|santiago|valpara|concepci|vi[ñn]a del mar|antofagasta|temuco|rancagua"
                          r"|south america|sudam|latin america|latam|anywhere in the world|worldwide", re.I)
REMOTE = re.compile(r"^\s*remot", re.I)
MESES = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
MESES.update({"ene": 1, "abr": 4, "ago": 8, "dic": 12})


def fecha_de_tarjeta(texto: str, hoy: str) -> str:
    """«Nov 03» → ISO. El año no viene: es el de hoy, salvo que la fecha quedara en el futuro (diciembre visto en enero)."""
    m = re.match(r"\s*([A-Za-z]{3})\w*\s+(\d{1,2})", texto or "")
    if not m or m.group(1).lower() not in MESES:
        return ""
    ref = date.fromisoformat(hoy)
    candidata = date(ref.year, MESES[m.group(1).lower()], int(m.group(2)))
    if candidata > ref:
        candidata = date(ref.year - 1, candidata.month, candidata.day)
    return candidata.isoformat()


def _texto(el) -> str:
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True)) if el is not None else ""


def _tarjeta(card, categoria: str, hoy: str) -> dict:
    titulo = _texto(card.select_one("h4.results-list-title strong"))
    info = _texto(card.select_one("div.size0.flex"))
    company = info.split("·")[0].strip()
    loc = card.select_one("span.location")
    tooltip = loc.select_one("div.location-tooltip-content") if loc is not None else None
    detalle = _texto(tooltip)
    if tooltip is not None:
        tooltip.extract()   # su texto viene dentro de span.location: se saca para que `lugar` sea solo la ciudad o «Remote»
    lugar = _texto(loc)
    residencia = " ".join((loc.select_one("[title]").get("title") or "").split()) if loc is not None and loc.select_one("[title]") else ""
    badges = _texto(card.select_one("div.gb-results-list__badges"))
    salary = re.sub(r"^\s*New\s*", "", badges).strip()
    fecha = _texto(card.select_one("div.opacity-half.size0"))
    resumen = re.sub(r"^\W+", "", " ".join((card.get("title") or "").split()))
    es_remoto = bool(REMOTE.match(lugar))
    donde = " ".join(p for p in (lugar, detalle, residencia) if p)
    return {
        "site": "getonbrd",
        "title": titulo,
        "company": company,
        "location": donde,
        "job_url": card.get("href", ""),
        "date_posted": fecha_de_tarjeta(fecha, hoy),
        "description": " ".join(p for p in (resumen, residencia) if p),
        "is_remote": es_remoto,
        "pais": "Chile" if ADMITE_CHILE.search(donde) else lugar.split("(")[0].strip(),
        "salary": salary,
        "search_query": f"getonbrd:{categoria}",
    }


def parse_listing(html: str, categoria: str = "programacion", hoy: str | None = None) -> list:
    hoy = hoy or date.today().isoformat()
    soup = BeautifulSoup(html, "html.parser")
    return [_tarjeta(card, categoria, hoy) for card in soup.select("a.results-item") if card.get("href")]


def http_get_listing(categoria: str) -> str:
    response = requests.get(f"{BASE}/jobs/{categoria}", headers=HEADERS, timeout=TIMEOUT)
    if response.status_code != 200:
        raise RuntimeError(f"GetOnBoard respondió {response.status_code}")
    return response.text


def scrape_getonbrd(fetch_listing=http_get_listing, categories=CATEGORIES, hoy: str | None = None, sleep=None) -> pd.DataFrame:
    """Un DataFrame con la misma forma que los de JobSpy. Una falla en una categoría no tira la otra."""
    pause = sleep or (lambda: time.sleep(random.uniform(*LISTING_SLEEP)))
    filas = []
    for i, categoria in enumerate(categories):
        if i:
            pause()
        try:
            html = fetch_listing(categoria)
        except Exception as error:
            print(f"  [getonbrd] {categoria}: {error}")
            continue
        tarjetas = parse_listing(html, categoria, hoy)
        print(f"  [getonbrd] {categoria}: {len(tarjetas)} avisos")
        filas.extend(tarjetas)
    df = pd.DataFrame(filas)
    return df.drop_duplicates(subset=["job_url"], keep="first").reset_index(drop=True) if len(df) else df
