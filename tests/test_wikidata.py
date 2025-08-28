from __future__ import annotations

import json
from typing import Any, Dict

import pytest

from autoniche.wikidata import run_sparql, fetch_item, Item


class _Resp:
    def __init__(self, payload: Dict[str, Any], status: int = 200) -> None:
        self._payload = payload
        self.status_code = status

    def json(self) -> Dict[str, Any]:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")



def test_run_sparql_parses_qids(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "results": {
            "bindings": [
                {"item": {"value": "http://www.wikidata.org/entity/Q1"}},
                {"item": {"value": "https://www.wikidata.org/entity/Q2"}},
            ]
        }
    }

    def mock_post(url: str, data: Dict[str, str], headers: Dict[str, str], timeout: int):  # type: ignore[override]
        return _Resp(payload)

    monkeypatch.setattr("autoniche.wikidata.requests.post", mock_post)
    qids = run_sparql("SELECT ?item WHERE { VALUES ?item { wd:Q1 wd:Q2 } }")
    assert set(qids) == {"Q1", "Q2"}



def test_fetch_item_parses_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    sparql_payload = {
        "results": {
            "bindings": [
                {
                    "itemLabel": {"value": "Test Park"},
                    "desc": {"value": "Opis"},
                    "inception": {"value": "1980-01-01T00:00:00Z"},
                    "coord": {"value": "Point(19.94 50.06)"},
                    "website": {"value": "https://example.org"},
                    "image": {"value": "https://commons.wikimedia.org/wiki/Special:FilePath/Example.jpg"},
                }
            ]
        }
    }
    commons_payload = {
        "query": {
            "pages": {
                "1": {
                    "imageinfo": [
                        {
                            "descriptionurl": "https://commons.wikimedia.org/wiki/File:Example.jpg",
                            "extmetadata": {
                                "LicenseShortName": {"value": "CC BY-SA"},
                                "Artist": {"value": "Autor"},
                            },
                        }
                    ]
                }
            }
        }
    }

    def mock_post(url: str, data, headers, timeout):  # type: ignore[override]
        return _Resp(sparql_payload)

    def mock_get(url: str, params, timeout):  # type: ignore[override]
        return _Resp(commons_payload)

    monkeypatch.setattr("autoniche.wikidata.requests.post", mock_post)
    monkeypatch.setattr("autoniche.wikidata.requests.get", mock_get)

    item = fetch_item("Q999")
    assert isinstance(item, Item)
    assert item.title == "Test Park"
    assert item.inception_year == 1980
    assert item.lat == pytest.approx(50.06)
    assert item.lon == pytest.approx(19.94)
    assert item.website == "https://example.org"
    assert item.image_page and "File:Example.jpg" in item.image_page
