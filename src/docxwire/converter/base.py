from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


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
