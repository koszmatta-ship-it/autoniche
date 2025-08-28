from __future__ import annotations

from pathlib import Path

from autoniche.config import Config, SiteConfig, NicheConfig, AffiliateLink
from autoniche.site import write_post, render_index, render_rss
from autoniche.wikidata import Item


def _cfg(tmp: Path) -> Config:
    site = SiteConfig(
        name="Test Site",
        base_url="https://example.com",
        output_dir=str(tmp / "docs"),
        language="pl",
        items_per_run=1,
        enable_images=False,
        enable_rss=True,
    )
    niche = NicheConfig(name="Test", sparql="SELECT {} WHERE {}")
    return Config(site=site, niche=niche, affiliate_insert="Rek.", affiliate_links=[AffiliateLink(label="L1", url="https://x")])


def test_write_post_and_index_and_rss(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)
    item = Item(
        qid="Q1",
        title="Testowy Park Narodowy",
        description="Opis",
        inception_year=1980,
        lat=50.06,
        lon=19.94,
        website="https://example.org",
        image_file=None,
        image_page=None,
        image_license=None,
        image_author=None,
    )
    md_path = write_post(cfg, item)
    assert Path(md_path).exists()

    render_index(cfg)
    assert Path(cfg.site.output_dir, "index.html").exists()

    render_rss(cfg)
    assert Path(cfg.site.output_dir, "rss.xml").exists()
