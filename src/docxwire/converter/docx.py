from __future__ import annotations

import re
import shutil
import tempfile
from pathlib import Path

import pypandoc
from bs4 import BeautifulSoup

from docxwire.converter.base import AbstractConverter, Article, Image, slugify

_HEADING_RE = re.compile(r"^h[1-6]$")


def _flag_lead_images(images: list[Image], lead_srcs: list[str]) -> None:
    """Set is_lead on images matching a lead <img> src.

    Raises ValueError when a lead src has no matching extracted media file.
    """
    if not lead_srcs:
        return
    lead_names = {Path(src).name for src in lead_srcs}
    matched: set[str] = set()
    for image in images:
        name = Path(image.media_filename).name
        if name in lead_names:
            image.is_lead = True
            matched.add(name)
    unmatched = lead_names - matched
    if unmatched:
        raise ValueError(
            f"lead image has no matching extracted media file: {', '.join(sorted(unmatched))}"
        )


class DocxConverter(AbstractConverter):
    def convert(self, src: Path) -> Article:
        """Convert a .docx file to an article with raw HTML output."""
        media_dir = tempfile.mkdtemp(prefix="media-")
        try:
            fallback_title = src.stem
            html = pypandoc.convert_file(
                str(src),
                to="html-native_spans",
                format="docx+styles",
                extra_args=[
                    "--wrap=none",
                    "--strip-comments",
                    "--extract-media",
                    str(media_dir),
                ],
            )

            # Extract first heading as title, then remove it from body
            soup = BeautifulSoup(html, "html.parser")
            heading = soup.find(_HEADING_RE)
            lead_srcs: list[str] = []
            if heading:
                title: str = heading.get_text()
                # Images in document order before the first heading are lead
                # images: record their src and remove them from the body.
                for el in soup.find_all(True):
                    if el is heading:
                        break
                    if el.name == "img":
                        img_src = el.get("src")
                        if img_src:
                            lead_srcs.append(str(img_src))
                        # Must stay after the src read: attrs vanish on decompose.
                        el.decompose()
                heading.decompose()
            else:
                title = fallback_title

            images: list[Image] = []
            media_path = Path(media_dir)
            if media_path.exists():
                for file_path in media_path.glob("**/*"):
                    if file_path.is_file():
                        media_filename = str(file_path.relative_to(media_path))
                        data = file_path.read_bytes()
                        images.append(Image(media_filename=media_filename, data=data))

            _flag_lead_images(images, lead_srcs)

            return Article(
                source_file=src,
                title=title,
                slug=slugify(fallback_title),
                body=str(soup),
                images=images,
            )
        except (OSError, ValueError, RuntimeError) as exc:
            raise RuntimeError(f"conversion of {src.name} failed: {exc}") from exc
        finally:
            shutil.rmtree(media_dir, ignore_errors=True)
