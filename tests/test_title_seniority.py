"""Filtro de seniority en títulos: este perfil es semi senior, no se postula a senior/lead/gestión."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "job1"))
from helpers import _matches_excluded_title  # noqa: E402


@pytest.mark.parametrize("title", [
    "Senior Full Stack Developer",
    "SeniorNode.js Developer",
    "Sr Backend Developer",
    "Sr. Developer",
    "Desarrollador Sr.",
    "Sr/Developer",
    "Ingeniero de Software III",
    "Software Engineer IV",
    "Chief Technology Officer",
    "Staff Software Engineer",
    "Solutions Architect",
    "Arquitecto de Software",
    "Project Manager TI",
    "Experto en Node.js",
])
def test_senior_and_above_titles_are_excluded(title):
    assert _matches_excluded_title(title) is True


@pytest.mark.parametrize("title", [
    "Semi Senior Full Stack Developer",
    "Semi-Senior Node Developer",
    "Desarrollador Semi Sr. Backend",
    "Full Stack Developer",
    "Ingeniero de Software II",
    "Desarrollador Fullstack Jr",
    "Desarrollador React",
])
def test_semi_senior_and_regular_titles_are_kept(title):
    assert _matches_excluded_title(title) is False
