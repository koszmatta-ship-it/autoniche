from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional
import yaml


@dataclass
class AffiliateLink:
    label: str
    url: str


@dataclass
class SiteConfig:
    name: str
    base_url: str
    output_dir: str = "docs"
    language: str = "pl"
    items_per_run: int = 3
    enable_images: bool = False
    enable_rss: bool = True
    enable_bluesky: bool = False
    enable_telegram: bool = False


@dataclass
class NicheConfig:
    name: Optional[str] = None
    sparql: str = ""


@dataclass
class SocialConfig:
    bluesky_post_template: str = "Nowy wpis: {{ title }} — {{ url }}"
    telegram_post_template: str = "Nowy wpis: <b>{{ title }}</b>\n{{ url }}"


@dataclass
class Config:
    site: SiteConfig
    niche: NicheConfig
    affiliate_insert: str = ""
    affiliate_links: List[AffiliateLink] = field(default_factory=list)
    social: SocialConfig = field(default_factory=SocialConfig)

    @staticmethod
    def load(path: str = "config.yml") -> "Config":
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        site = SiteConfig(**raw.get("site", {}))
        niche = NicheConfig(**raw.get("niche", {}))
        aff = raw.get("affiliate", {})
        affiliate_insert = aff.get("insert_paragraph", "")
        affiliate_links = [AffiliateLink(**x) for x in aff.get("links", [])]
        social_raw = raw.get("social", {})
        social = SocialConfig(
            bluesky_post_template=social_raw.get("bluesky", {}).get("post_template", SocialConfig().bluesky_post_template),
            telegram_post_template=social_raw.get("telegram", {}).get("post_template", SocialConfig().telegram_post_template),
        )
        return Config(
            site=site,
            niche=niche,
            affiliate_insert=affiliate_insert,
            affiliate_links=affiliate_links,
            social=social,
        )

    @staticmethod
    def env(key: str, default: Optional[str] = None) -> Optional[str]:
        # Env indirection keeps secrets out of repo.
        return os.getenv(key, default)
