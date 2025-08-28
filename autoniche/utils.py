from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List
from slugify import slugify
import pytz

WARSAW_TZ = pytz.timezone("Europe/Warsaw")


def load_state(path: str = "data/state.json") -> Dict:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if not Path(path).exists():
        return {"processed_qids": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state: Dict, path: str = "data/state.json") -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def today_iso() -> str:
    # Align publishing to Warsaw timezone to avoid confusing dates.
    return datetime.now(WARSAW_TZ).strftime("%Y-%m-%d")


def make_slug(title: str) -> str:
    s = slugify(title, lowercase=True)
    return re.sub(r"-+", "-", s)
