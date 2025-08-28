from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape
from feedgen.feed import FeedGenerator

from .config import Config
from .utils import make_slug, today_iso
from .wikidata import Item


def _env() -> Environment:
    here = Path(__file__).parent
    env = Environment(
        loader=FileSystemLoader(str(here / "templates")),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    return env


def render_post(cfg: Config, item: Item) -> str:
    env = _env()
    tpl = env.get_template("post.md.j2")
    return tpl.render(
        site=cfg.site,
        item=item,
        date=today_iso(),
        affiliate_insert=cfg.affiliate_insert,
        affiliate_links=cfg.affiliate_links,
    )


def write_post(cfg: Config, item: Item) -> str:
    slug = make_slug(item.title)
    post_dir = Path(cfg.site.output_dir) / "posts"
    post_dir.mkdir(parents=True, exist_ok=True)
    path = post_dir / f"{today_iso()}-{slug}.md"
    content = render_post(cfg, item)
    path.write_text(content, encoding="utf-8")
    return str(path)


def render_index(cfg: Config) -> None:
    env = _env()
    tpl = env.get_template("index.html.j2")
    posts_dir = Path(cfg.site.output_dir) / "posts"
    posts = sorted(posts_dir.glob("*.md"), reverse=True)
    html = tpl.render(site=cfg.site, posts=[p.name for p in posts])
    Path(cfg.site.output_dir, "index.html").write_text(html, encoding="utf-8")


def render_rss(cfg: Config) -> None:
    if not cfg.site.enable_rss:
        return
    posts_dir = Path(cfg.site.output_dir) / "posts"
    posts = sorted(posts_dir.glob("*.md"), reverse=True)[:50]

    fg = FeedGenerator()
    fg.id(cfg.site.base_url)
    fg.title(cfg.site.name)
    fg.link(href=cfg.site.base_url, rel='alternate')
    fg.language(cfg.site.language)

    for p in posts:
        raw = p.read_text(encoding="utf-8")
        # naive parse: front matter line 1 is title in markdown H1
        first_line = next((line for line in raw.splitlines() if line.startswith("# ")), "# Wpis").strip("# ").strip()
        url = f"{cfg.site.base_url}/posts/{p.name.replace('.md', '.html')}"
        fe = fg.add_entry()
        fe.id(url)
        fe.title(first_line)
        fe.link(href=url)
        fe.published(datetime.fromisoformat(p.name[:10]))
    Path(cfg.site.output_dir, "rss.xml").write_bytes(fg.rss_str(pretty=True))
