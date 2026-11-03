"""Filtro de relevancia.

Hoy pasa si score ≥ mínimo O el título dice developer/engineer: con descripción vacía (LinkedIn)
eso dejaba entrar Elixir/.NET/Perl con score 0 (13/53 el 03-11). Con texto disponible manda el
score; el bypass por título queda solo para filas sin descripción (recall donde no hay más datos).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "job1"))
from helpers import passes_relevance  # noqa: E402

MIN = 2


def row(score, title, description):
    return {"match_score": score, "title": title, "description": description}


def test_score_at_or_above_minimum_passes():
    assert passes_relevance(row(2, "Cocinero", "x"), MIN) is True


def test_low_score_with_description_fails_even_if_title_says_developer():
    assert passes_relevance(row(0, "Elixir Developer", "Agentic Elixir, Phoenix, OTP"), MIN) is False


def test_low_score_without_description_passes_if_title_is_a_dev_role():
    assert passes_relevance(row(0, "Software Engineer", ""), MIN) is True
    assert passes_relevance(row(0, "Desarrollador Full Stack", None), MIN) is True


def test_low_score_without_description_and_non_dev_title_fails():
    assert passes_relevance(row(0, "Analista de Soporte", ""), MIN) is False
