"""Salud de la corrida: lo que el correo dice cuando algo se rompió sin avisar (v10.6).

Cada fuente falla en silencio (un `except` imprime y sigue), así que un portal que cambia su HTML deja de
aportar filas y el correo llega igual, con menos avisos. Acá se cuentan las filas CRUDAS por fuente, antes
de cualquier filtro, y se mide cuánto pasó desde la última corrida que trajo datos.
"""
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re

from config import FUENTES_ESENCIALES, FUENTES_ESPERADAS, MAX_HORAS_ENTRE_CORRIDAS

MARCA_AVISO = "⚠"
RUN_ID_FORMAT = "%Y%m%d_%H%M"
RUN_DIR_REGEX = re.compile(r"^\d{8}_\d{4}$")
TOTAL_HEADER_REGEX = re.compile(r"^# TOTAL_RESULTADOS=(\d+)")
SEGUNDOS_POR_HORA = 3600


@dataclass(frozen=True)
class SaludCorrida:
    fuentes: dict   # {sitio: filas crudas}
    avisos: tuple   # frases para el asunto y la cabecera del correo; vacío = corrida sana

    @property
    def sin_datos(self) -> bool:
        return sum(self.fuentes.values()) == 0


def contar_por_fuente(frames: list, esperadas=FUENTES_ESPERADAS) -> dict:
    """Filas crudas por sitio. Una fuente esperada que no trajo nada queda en 0, no ausente.
    Sin red, JobSpy devuelve DataFrames sin columnas: cuentan 0."""
    conteo = {fuente: 0 for fuente in esperadas}
    for frame in frames:
        if "site" not in frame.columns:
            continue
        for sitio, filas in frame["site"].value_counts().items():
            conteo[sitio] = conteo.get(sitio, 0) + int(filas)
    return conteo


def _total_de_la_corrida(run_dir: Path) -> int:
    """El TOTAL_RESULTADOS de la cabecera de results.csv; 0 si no hay archivo o no trae la línea."""
    csv_path = run_dir / "results.csv"
    if not csv_path.exists():
        return 0
    with open(csv_path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.startswith("#"):
                break
            match = TOTAL_HEADER_REGEX.match(line)
            if match:
                return int(match.group(1))
    return 0


def ultima_corrida_con_datos(job_dir: Path, antes_de: str) -> str | None:
    """El run_id más reciente, anterior a `antes_de`, cuya carpeta tiene resultados. Las carpetas con 0 filas
    (el radar híbrido las dejó durante la caída del 07 al 09-11) no cuentan."""
    anteriores = sorted(
        (p.name for p in Path(job_dir).iterdir() if p.is_dir() and RUN_DIR_REGEX.match(p.name) and p.name < antes_de),
        reverse=True,
    )
    for run_id in anteriores:
        if _total_de_la_corrida(Path(job_dir) / run_id) > 0:
            return run_id
    return None


def _horas_entre(desde: str, hasta: str) -> int:
    delta = datetime.strptime(hasta, RUN_ID_FORMAT) - datetime.strptime(desde, RUN_ID_FORMAT)
    return round(delta.total_seconds() / SEGUNDOS_POR_HORA)


def evaluar_salud(frames: list, job_dir: Path, run_id: str, esperadas=FUENTES_ESPERADAS,
                  esenciales=FUENTES_ESENCIALES, max_horas: int = MAX_HORAS_ENTRE_CORRIDAS) -> SaludCorrida:
    fuentes = contar_por_fuente(frames, esperadas)
    avisos = []

    en_cero = [fuente for fuente in esenciales if fuentes.get(fuente, 0) == 0]
    if en_cero:
        etiqueta = "fuente en 0" if len(en_cero) == 1 else "fuentes en 0"
        avisos.append(f"{etiqueta}: {', '.join(en_cero)}")

    ultima = ultima_corrida_con_datos(job_dir, antes_de=run_id)
    if ultima is not None:
        horas = _horas_entre(ultima, run_id)
        if horas > max_horas:
            avisos.append(f"sin corridas con datos desde {ultima} ({horas} h)")

    return SaludCorrida(fuentes=fuentes, avisos=tuple(avisos))


def linea_de_fuentes(salud: SaludCorrida) -> str:
    return "fuentes: " + " · ".join(f"{fuente} {filas}" for fuente, filas in salud.fuentes.items())
