from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from .config import Config
from .utils import load_state, save_state
from .wikidata import run_sparql, fetch_item
from .site import write_post, render_index, render_rss
from .social import post_bluesky, post_telegram


def _pick_new_qids(all_qids: List[str], processed: List[str], limit: int) -> List[str]:
    fresh = [q for q in all_qids if q not in processed]
    return fresh[:limit]


def generate(cfg: Config) -> List[str]:
    state = load_state()
    all_qids = run_sparql(cfg.niche.sparql)
    if not all_qids:
        raise SystemExit("SPARQL nie zwrócił wyników — doprecyzuj niszę.")
    to_do = _pick_new_qids(all_qids, state.get("processed_qids", []), cfg.site.items_per_run)
    if not to_do:
        # Reset when exhausted — new round starts.
        state["processed_qids"] = []
        save_state(state)
        to_do = _pick_new_qids(all_qids, [], cfg.site.items_per_run)

    created_paths: List[str] = []
    for qid in to_do:
        item = fetch_item(qid, lang=cfg.site.language)
        md_path = write_post(cfg, item)
        created_paths.append(md_path)
        state.setdefault("processed_qids", []).append(qid)
    save_state(state)

    render_index(cfg)
    render_rss(cfg)
    return created_paths


def post_socials(cfg: Config, md_paths: List[str]) -> None:
    for p in md_paths:
        post_bluesky(cfg, p)
        post_telegram(cfg, p)


def run_all() -> None:
    cfg = Config.load()
    created = generate(cfg)
    post_socials(cfg, created)


def main() -> None:
    parser = argparse.ArgumentParser(description="AutoNiche content pipeline")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("run-all")
    sub.add_parser("generate")
    sub.add_parser("post")
    args = parser.parse_args()

    if args.cmd in ("run-all", None):
        run_all()
    elif args.cmd == "generate":
        cfg = Config.load()
        generate(cfg)
    elif args.cmd == "post":
        cfg = Config.load()
        docs = Path(cfg.site.output_dir) / "posts"
        latest = sorted(docs.glob("*.md"), reverse=True)[:cfg.site.items_per_run]
        post_socials(cfg, [str(p) for p in latest])


if __name__ == "__main__":
    main()
