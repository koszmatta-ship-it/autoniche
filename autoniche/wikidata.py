from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional
import requests

WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"


@dataclass
class Item:
    qid: str
    title: str
    description: Optional[str]
    inception_year: Optional[int]
    lat: Optional[float]
    lon: Optional[float]
    website: Optional[str]
    image_file: Optional[str]
    image_page: Optional[str]
    image_license: Optional[str]
    image_author: Optional[str]


def run_sparql(ids_sparql: str) -> List[str]:
    r = requests.post(
        WIKIDATA_SPARQL,
        data={"query": ids_sparql},
        headers={"Accept": "application/sparql-results+json", "User-Agent": "AutoNiche/1.0 (https://github.com/)"},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    items: List[str] = []
    for b in data.get("results", {}).get("bindings", []):
        uri = b.get("item", {}).get("value")
        if not uri:
            for k in ("s", "x", "entity"):
                if k in b:
                    uri = b[k]["value"]
                    break
        if not uri:
            continue
        if uri.startswith("http://www.wikidata.org/entity/") or uri.startswith("https://www.wikidata.org/entity/"):
            qid = uri.rsplit("/", 1)[-1]
            items.append(qid)
    random.shuffle(items)
    return items


def fetch_item(qid: str, lang: str = "pl") -> Item:
    query = f"""
    SELECT ?item ?itemLabel ?desc ?inception ?coord ?website ?image WHERE {{
      VALUES ?item {{ wd:{qid} }}
      OPTIONAL {{ ?item schema:description ?desc FILTER(LANG(?desc)='{lang}'). }}
      OPTIONAL {{ ?item wdt:P571 ?inception. }}
      OPTIONAL {{ ?item wdt:P625 ?coord. }}
      OPTIONAL {{ ?item wdt:P856 ?website. }}
      OPTIONAL {{ ?item wdt:P18 ?image. }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language '{lang},en' }}
    }}
    """
    r = requests.post(
        WIKIDATA_SPARQL,
        data={"query": query},
        headers={"Accept": "application/sparql-results+json", "User-Agent": "AutoNiche/1.0 (https://github.com/)"},
        timeout=30,
    )
    r.raise_for_status()
    rows = r.json().get("results", {}).get("bindings", [])
    if not rows:
        return Item(qid=qid, title=qid, description=None, inception_year=None, lat=None, lon=None, website=None, image_file=None, image_page=None, image_license=None, image_author=None)
    row = rows[0]

    def v(key: str) -> Optional[str]:
        return row.get(key, {}).get("value")

    title = v("itemLabel") or qid
    desc = v("desc")
    inception_year = None
    if v("inception"):
        inception_year = int(v("inception")[:4])

    lat = lon = None
    if v("coord"):
        wkt = v("coord").replace("Point(", "").replace(")", "").strip()
        parts = wkt.split()
        if len(parts) == 2:
            # WKT uses order: lon lat
            lon = float(parts[0])
            lat = float(parts[1])

    website = v("website")

    image_file = None
    image_page = None
    image_license = None
    image_author = None
    if v("image"):
        image_file = v("image").rsplit("/", 1)[-1]
        try:
            meta = requests.get(
                "https://commons.wikimedia.org/w/api.php",
                params={
                    "action": "query",
                    "prop": "imageinfo",
                    "iiprop": "extmetadata|url",
                    "titles": f"File:{image_file}",
                    "format": "json",
                },
                timeout=30,
            ).json()
            pages = meta.get("query", {}).get("pages", {})
            if pages:
                info = next(iter(pages.values())).get("imageinfo", [{}])[0]
                image_page = info.get("descriptionurl")
                ext = info.get("extmetadata", {})
                image_license = (ext.get("LicenseShortName", {}) or {}).get("value")
                image_author = (ext.get("Artist", {}) or {}).get("value")
        except Exception:
            pass

    return Item(
        qid=qid,
        title=title,
        description=desc,
        inception_year=inception_year,
        lat=lat,
        lon=lon,
        website=website,
        image_file=image_file,
        image_page=image_page,
        image_license=image_license,
        image_author=image_author,
    )
