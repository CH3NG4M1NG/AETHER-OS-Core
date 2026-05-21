from __future__ import annotations

import re

import requests


class WebAccessEngine:
    """Allows the AI runtime to fetch web content as structured context."""

    def __init__(self, timeout: int = 8) -> None:
        self.timeout = timeout

    def fetch(self, url: str, max_chars: int = 1200) -> dict:
        resp = requests.get(url, timeout=self.timeout, headers={"User-Agent": "AETHER-OS/1.0"})
        resp.raise_for_status()
        text = re.sub(r"\s+", " ", resp.text)
        return {"url": url, "status": resp.status_code, "excerpt": text[:max_chars]}
