"""Dependabot (16-11): soupsieve tenía 6 alertas abiertas y solo las cierra la 4.0.0. El lock es lo que instala el deploy."""
import json
from pathlib import Path

import pytest

LOCK = Path(__file__).parent.parent / "Pipfile.lock"
MIN_VERSIONS = {"soupsieve": (4, 0)}


def locked_version(package: str) -> tuple:
    pinned = json.loads(LOCK.read_text(encoding="utf-8"))["default"][package]["version"]
    return tuple(int(part) for part in pinned.removeprefix("==").split("."))


@pytest.mark.parametrize("package", sorted(MIN_VERSIONS))
def test_locked_version_is_at_or_above_the_one_that_fixes_the_dependabot_alerts(package):
    assert locked_version(package) >= MIN_VERSIONS[package]


def test_soupsieve_lock_entry_declares_the_python_it_needs_and_has_hashes():
    entry = json.loads(LOCK.read_text(encoding="utf-8"))["default"]["soupsieve"]
    assert len(entry["hashes"]) >= 1 and all(h.startswith("sha256:") for h in entry["hashes"])
    assert "3.11.5" in entry["markers"]   # soupsieve 4.0 exige Python >= 3.11.5
