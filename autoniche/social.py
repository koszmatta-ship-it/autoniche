from __future__ import annotations

import html
import os
from pathlib import Path
from typing import Optional

from jinja2 import Template

from .config import Config


def _read_title_and_url(cfg: Config, md_path: str) -> tuple[str, str]:
    name = Path(md_path).name
    title = "Wpis"
    with open(md_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("# "):
                title = line[2:].strip()
                break
    url = f"{cfg.site.base_url}/posts/{name.replace('.md', '.html')}"
    return title, url


def post_bluesky(cfg: Config, md_path: str) -> Optional[str]:
    if not cfg.site.enable_bluesky:
        return None
    handle = os.getenv("BLUESKY_HANDLE")
    password = os.getenv("BLUESKY_PASSWORD")
    if not handle or not password:
        return "BLUESKY creds missing; skipped"
    from atproto import Client

    title, url = _read_title_and_url(cfg, md_path)
    text = Template(cfg.social.bluesky_post_template).render(title=title, url=url)

    c = Client()
    c.login(handle, password)
    c.send_post(text)
    return "Posted to Bluesky"


def post_telegram(cfg: Config, md_path: str) -> Optional[str]:
    if not cfg.site.enable_telegram:
        return None
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    channel = os.getenv("TELEGRAM_CHANNEL")
    if not token or not channel:
        return "Telegram creds missing; skipped"

    import requests

    title, url = _read_title_and_url(cfg, md_path)
    text = Template(cfg.social.telegram_post_template).render(title=html.escape(title), url=url)
    r = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": channel, "text": text, "parse_mode": "HTML", "disable_web_page_preview": False},
        timeout=30,
    )
    try:
        r.raise_for_status()
        return "Posted to Telegram"
    except Exception as e:
        return f"Telegram error: {e}"
