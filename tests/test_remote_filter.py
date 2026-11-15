"""Filtro de modalidad.

LinkedIn se consulta con `is_remote=True` (f_WT=2): todo lo que devuelve es remoto SEGÚN LINKEDIN.
Exigirle además la palabra "remote" en el texto tiraba 608 de 685 descartes por corrida (03-11);
Kraken "Fullstack Engineer" tiene 5.658 chars de descripción y no dice "remote" en ninguno.
Indeed/Glassdoor no se consultan con ese filtro → siguen necesitando la keyword.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "job1"))
from helpers import is_likely_remote  # noqa: E402


def row(site, title="Fullstack Engineer", description="", location="Chile"):
    return {"site": site, "title": title, "description": description, "location": location}


def test_linkedin_job_without_remote_keyword_is_still_remote():
    assert is_likely_remote(row("linkedin", description="Building the future of open finance")) is True


def test_linkedin_job_that_says_hibrido_in_title_is_not_remote():
    assert is_likely_remote(row("linkedin", title="Full-Stack Engineer - Híbrido")) is False


def test_linkedin_vague_wording_in_description_does_not_decide_modality():
    """'no presencial', 'hybrid cloud' y 'apps híbridas' aparecen en avisos remotos (review 03-11): solo
    las frases explícitas de modalidad en la descripción descartan (medido 14-11: 73 de 269 híbridos)."""
    for text in ("Trabajo 100% remoto, no presencial", "Experience with hybrid cloud", "Desarrollo de apps híbridas con Ionic"):
        assert is_likely_remote(row("linkedin", description=text)) is True, text


@pytest.mark.parametrize("text", [
    "Modalidad presencial en Las Condes",
    "Modalidad: híbrida, con base en Santiago",
    "Trabajo híbrido 3 días a la semana",
    "Esquema de trabajo híbrido",
    "Jornada híbrida",
    "Formato hibrido",
    "Cargo híbrido en Providencia",
    "Modelo híbrido con oficina en Bogotá",
    "Se requieren 3 días a la semana de forma presencial",
    "Debes asistir 2 días en la oficina",
    "3 días presencial",
    "Requiere asistencia presencial",
    "Se trabaja de forma presencial en nuestras oficinas",
])
def test_linkedin_description_saying_hybrid_or_onsite_is_not_remote(text):
    assert is_likely_remote(row("linkedin", description=text)) is False


@pytest.mark.parametrize("text", [
    "100% remota, no presencial",
    "Trabajo sin asistencia presencial",
    "No requiere asistencia presencial",
    "Modalidad no presencial",
    "Modalidad: ni híbrida ni presencial",
])
def test_linkedin_description_negating_presencial_stays_remote(text):
    assert is_likely_remote(row("linkedin", description=text)) is True, text


def test_linkedin_negation_does_not_cancel_a_later_onsite_phrase():
    text = "Equipo no grande. Modalidad presencial en Las Condes"
    assert is_likely_remote(row("linkedin", description=text)) is False


def test_linkedin_job_with_on_site_in_location_is_not_remote():
    assert is_likely_remote(row("linkedin", location="Santiago · On-site")) is False


def test_indeed_job_without_remote_keyword_is_not_remote():
    assert is_likely_remote(row("indeed", description="Gran equipo, oficinas en Providencia")) is False


def test_indeed_job_with_home_office_is_remote():
    assert is_likely_remote(row("indeed", description="Trabajo 100% home office")) is True


def test_glassdoor_job_with_remote_in_location_is_remote():
    assert is_likely_remote(row("glassdoor", location="Remote")) is True
