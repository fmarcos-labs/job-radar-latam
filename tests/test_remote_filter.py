"""Filtro de modalidad.

LinkedIn se consulta con `is_remote=True` (f_WT=2): todo lo que devuelve es remoto SEGÚN LINKEDIN.
Exigirle además la palabra "remote" en el texto tiraba 608 de 685 descartes por corrida (03-11);
Kraken "Fullstack Engineer" tiene 5.658 chars de descripción y no dice "remote" en ninguno.
Indeed/Glassdoor no se consultan con ese filtro → siguen necesitando la keyword.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "job1"))
from helpers import is_likely_remote  # noqa: E402


def row(site, title="Fullstack Engineer", description="", location="Chile"):
    return {"site": site, "title": title, "description": description, "location": location}


def test_linkedin_job_without_remote_keyword_is_still_remote():
    assert is_likely_remote(row("linkedin", description="Building the future of open finance")) is True


def test_linkedin_job_that_says_hibrido_in_title_is_not_remote():
    assert is_likely_remote(row("linkedin", title="Full-Stack Engineer - Híbrido")) is False


def test_linkedin_description_wording_does_not_decide_modality():
    """La descripción NO decide en LinkedIn: 'no presencial', 'hybrid cloud' y 'entrevistas on-site'
    aparecen en avisos remotos (review 03-11). La señal va en título y ubicación."""
    assert is_likely_remote(row("linkedin", description="Modalidad presencial en Las Condes")) is True


def test_linkedin_job_with_on_site_in_location_is_not_remote():
    assert is_likely_remote(row("linkedin", location="Santiago · On-site")) is False


def test_indeed_job_without_remote_keyword_is_not_remote():
    assert is_likely_remote(row("indeed", description="Gran equipo, oficinas en Providencia")) is False


def test_indeed_job_with_home_office_is_remote():
    assert is_likely_remote(row("indeed", description="Trabajo 100% home office")) is True


def test_glassdoor_job_with_remote_in_location_is_remote():
    assert is_likely_remote(row("glassdoor", location="Remote")) is True
