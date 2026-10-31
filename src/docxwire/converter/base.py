from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


def slugify(text: str) -> str:
    """Convert arbitrary text into a URL-safe slug.

    If *text* starts with a ``YYYY[-.]MM`` date prefix it is moved
    to the end (e.g. ``2025.04 Ruderkurs`` → ``ruderkurs-2025-04``).
    """
    text = text.strip()

    # Detect leading date-prefixed pattern like "2025.04" or "2024-12"
    m = re.match(r"(?:^|\s*)(\d{4}[./\-]\d{2})(\s*.+)?", text)
    if m:
        date_part: str = m.group(1)
        rest: str = (m.group(2) or "").strip()
        parts: list[str] = [rest, date_part] if rest else [date_part]
        text = " ".join(p for p in parts if p)

    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text


@dataclass
class Image:
    """Single article image."""

    media_filename: str
    data: bytes = b""
    caption: str = ""
    alt: str = ""
    upload_path: str = ""
    is_lead: bool = False


@dataclass
class Article:
    """Carries all data needed to produce and publish an article."""

    source_file: Path
    title: str = ""
    slug: str = ""
    body: str = ""
    catid: int = 0
    created_date: str = ""
    publish_up: str = ""
    metadesc: str = ""
    metakey: str = ""
    tags: list[str] = field(default_factory=list)
    note: str = ""
    created_by_alias: str = ""
    images: list[Image] = field(default_factory=list)


class AbstractConverter(ABC):
    """Interface for document converters."""

    @abstractmethod
    def convert(self, src: Path) -> Article:
        """Convert a source document, returning filled Article."""
        ...
