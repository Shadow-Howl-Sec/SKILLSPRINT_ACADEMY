"""Link metadata fetcher (plan §5.7, offline plan §2.1 / §6.2).

Two modes:
  - OFFLINE_MODE (or no network) → look the URL up in the local
    `CachedResource` table (populated once by `sync_resource_cache.ps1`).
    If found, return the cached title/resource_type. If not, fall back to a
    plain "manually entered, unavailable offline" stub.
  - Online → live OpenGraph/<title> scraping with SSRF protection
    (preserved from the original implementation).
"""
from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse
from typing import Optional

import requests
from bs4 import BeautifulSoup

from flask import current_app


_USER_AGENT = ("Mozilla/5.0 (compatible; SkillSprintLinkBot/1.0; "
               "+https://skillsprint.academy/bot)")


def _classify(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    if "youtube.com" in host or "youtu.be" in host:
        return "video"
    if "udemy.com" in host:
        return "course"
    if "github.com" in host:
        return "github"
    if url.lower().endswith(".pdf"):
        return "pdf"
    return "article"


def _classify_from_url(url: str) -> str:
    """Same as _classify but accounts for cached file paths (pdf extension)."""
    return _classify(url)


def _is_safe_url(url: str) -> bool:
    """Reject loopback / private / link-local IPs to mitigate SSRF."""
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if parsed.scheme not in ("http", "https"):
        return False
    host = parsed.hostname
    if not host:
        return False
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False
    for _family, _stype, _proto, _canon, sockaddr in infos:
        ip_str = sockaddr[0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            return False
        if (ip.is_private or ip.is_loopback or ip.is_link_local
                or ip.is_multicast or ip.is_reserved):
            return False
    return True


def _cache_lookup(url: str) -> Optional[dict]:
    """Read from CachedResource table for a previously-synced copy."""
    try:
        from models import CachedResource
    except Exception:
        return None
    row = CachedResource.query.filter_by(original_url=url).first()
    if row is None:
        return None
    return {
        "title": (row.title or url)[:300],
        "thumbnail_url": None,
        "resource_type": row.resource_type or _classify(url),
        "cached": True,
        "local_path": row.local_path,
    }


def _offline_stub(url: str) -> dict:
    return {
        "title": url,
        "thumbnail_url": None,
        "resource_type": _classify(url),
        "unavailable_offline": True,
    }


def fetch_metadata(url: str, timeout: float = 8.0) -> dict:
    """Return {title, thumbnail_url, resource_type} or partial data on error.

    In OFFLINE_MODE this never makes an outbound HTTP call (plan §14).
    """
    base_stub = {"title": url, "thumbnail_url": None,
                 "resource_type": _classify(url)}

    # 1. Always check the local cache first (works both online and offline).
    cached = _cache_lookup(url)
    if cached is not None:
        return cached

    # 2. OFFLINE_MODE: never fetch live; return the placeholder.
    if current_app.config.get("OFFLINE_MODE", False):
        return _offline_stub(url)

    # 3. Online path: live fetch with SSRF protection (original behaviour).
    if not _is_safe_url(url):
        return base_stub
    try:
        resp = requests.get(url, timeout=timeout,
                            headers={"User-Agent": _USER_AGENT},
                            allow_redirects=True)
        resp.raise_for_status()
    except requests.RequestException:
        return base_stub

    soup = BeautifulSoup(resp.text[:200_000], "lxml")

    og_title = soup.find("meta", property="og:title")
    og_image = soup.find("meta", property="og:image")
    title_tag = soup.find("title")

    title = None
    if og_title and og_title.get("content"):
        title = og_title["content"].strip()
    elif title_tag and title_tag.string:
        title = title_tag.string.strip()
    if title:
        base_stub["title"] = title[:300]

    if og_image and og_image.get("content"):
        base_stub["thumbnail_url"] = og_image["content"][:500]

    return base_stub
