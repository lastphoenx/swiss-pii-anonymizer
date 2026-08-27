import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from swiss_pii_anonymizer.plz_catalog import is_known_ch_location, known_names_for_plz


def test_known_major_cities():
    assert is_known_ch_location("8001", "Zürich")
    assert is_known_ch_location("3007", "Bern")
    assert is_known_ch_location("4058", "Basel")
    assert is_known_ch_location("1201", "Genève")


def test_case_insensitive_match():
    assert is_known_ch_location("8001", "zürich")
    assert is_known_ch_location("8001", "ZÜRICH")


def test_unknown_plz_rejected():
    assert not is_known_ch_location("9999", "Nirgendwo")


def test_wrong_city_for_plz_rejected():
    assert not is_known_ch_location("8001", "Bern")


def test_known_names_for_plz_returns_multiple_when_shared():
    names = known_names_for_plz("3007")
    assert "Bern" in names
