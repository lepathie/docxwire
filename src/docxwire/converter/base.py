from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import ClassVar


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
    language: str = ""


class NoteItem(StrEnum):
    """The fixed metadata items a note can carry, with their German
    labels. Positional/role-based image references are plain strings and
    are not part of this vocabulary."""

    TITLE = "Titel"
    AUTHOR = "Autor"
    CREATED_DATE = "Erstellungsdatum"


class NoteBuilder:
    """Collects short review items and renders the one-line German note.

    Identical items are de-duplicated. Items render in a fixed order —
    the metadata items in the order of :attr:`metadata_order`, then the
    image references in the order they were added — independent of the
    order in which they were detected. ``build()`` returns ``""`` when
    nothing was added.
    """

    prefix = "Prüfe: "
    metadata_order: ClassVar[tuple[NoteItem, ...]] = (
        NoteItem.TITLE,
        NoteItem.AUTHOR,
        NoteItem.CREATED_DATE,
    )

    def __init__(self) -> None:
        self._metadata: set[NoteItem] = set()
        self._image_refs: list[str] = []

    def add(self, item: NoteItem) -> None:
        """Record one metadata item; duplicates are ignored."""
        self._metadata.add(item)

    def add_image_ref(self, ref: str) -> None:
        """Record one positional/role-based image reference; duplicates
        are ignored."""
        if ref not in self._image_refs:
            self._image_refs.append(ref)

    def build(self) -> str:
        """Render the collected items as ``Prüfe: <a>, <b>`` (or ``""``)."""
        items = [item.value for item in self.metadata_order if item in self._metadata]
        items.extend(self._image_refs)
        if not items:
            return ""
        return self.prefix + ", ".join(items)


class AbstractConverter(ABC):
    """Interface for document converters."""

    @abstractmethod
    def convert(self, src: Path) -> Article:
        """Convert a source document, returning filled Article."""
        ...
