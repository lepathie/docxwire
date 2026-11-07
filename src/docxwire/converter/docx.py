from __future__ import annotations

import re
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import TypeGuard
from xml.etree import ElementTree

import pypandoc
from bs4 import BeautifulSoup, Tag

from docxwire.converter.base import (
    AbstractConverter,
    Article,
    Image,
    NoteBuilder,
    NoteItem,
    slugify,
)

_HEADING_RE = re.compile(r"^h[1-6]$")
_CAPTION_STYLE = "Bildunterschrift"
_CORE_CREATED_TAG = "{http://purl.org/dc/terms/}created"
_AUTOR_STYLE = "Autor"
_AUTOR_LABEL_RE = re.compile(r"^Autor:\s*")


def _top_level_block(el: Tag, root: BeautifulSoup) -> Tag:
    """Return the top-level block *el* sits in (a direct child of *root*)."""
    node: Tag = el
    while True:
        parent = node.parent
        if not isinstance(parent, Tag) or parent is root:
            return node
        node = parent


def _next_block_sibling(block: Tag) -> Tag | None:
    """Return the next top-level sibling block of *block*, skipping the
    whitespace text nodes pandoc emits between blocks.
    """
    sibling = block.next_sibling
    while sibling is not None and not isinstance(sibling, Tag):
        sibling = sibling.next_sibling
    return sibling


def _is_caption_candidate(block: Tag | None) -> TypeGuard[Tag]:
    """True if *block* is a caption line: a non-heading, image-free,
    paragraph-shaped block (a ``<p>``, or a ``<div>`` wrapping a ``<p>``)
    with non-empty text.
    """
    if not isinstance(block, Tag) or block.name is None:
        return False
    if _HEADING_RE.match(block.name) or block.find("img") is not None:
        return False
    if not block.get_text(strip=True):
        return False
    if block.name == "p":
        return True
    children = block.find_all(True, recursive=False)
    return block.name == "div" and len(children) == 1 and children[0].name == "p"


def _apply_image_captions(images: list[Image], captions: dict[str, str]) -> None:
    """Set caption on each image whose media filename matches a captured
    caption, keyed by the <img> src (basename match, as in lead flagging).
    """
    if not captions:
        return
    by_name = {Path(src).name: text for src, text in captions.items()}
    for image in images:
        text = by_name.get(Path(image.media_filename).name)
        if text:
            image.caption = text


# Generic placeholder for lead images while lead-slot assignment does not
# exist yet; the single swap point when it lands.
_LEAD_SLOT_LABEL = "Titelbild"


def _lead_label(image: Image) -> str:
    """Return the lead-slot label the note uses to reference *image*.

    While lead-slot assignment does not exist, every lead image shares one
    generic placeholder label.
    """
    return _LEAD_SLOT_LABEL


def _inbody_ordinals(images: list[Image]) -> dict[str, int]:
    """Map media-file basenames to 1-based ordinals among in-body (non-lead)
    images, in list (document) order.
    """
    ordinals: dict[str, int] = {}
    position = 0
    for image in images:
        if image.is_lead:
            continue
        position += 1
        ordinals[Path(image.media_filename).name] = position
    return ordinals


def _condensed_ordinals(ordinals: list[int]) -> str:
    """Render 1-based *ordinals* condensed to one shared ``Bild``: numbers
    ascending, joined with `, ` and `& ` before the last
    (``1. & 2. Bild``, ``1., 2. & 3. Bild``).
    """
    numbers = [f"{n}." for n in sorted(set(ordinals))]
    if len(numbers) == 1:
        return f"{numbers[0]} Bild"
    return f"{', '.join(numbers[:-1])} & {numbers[-1]} Bild"


def _guessed_caption_items(images: list[Image], guessed_srcs: list[str]) -> list[str]:
    """Return the note items for images whose caption was captured from a
    line lacking the Bildunterschrift style, i.e. guessed.

    In-body images are referenced by a condensed in-body ordinal; lead
    images by their lead-slot label. Images without a matching extracted
    media file are ignored.
    """
    if not guessed_srcs:
        return []
    by_name = {Path(image.media_filename).name: image for image in images}
    ordinals = _inbody_ordinals(images)
    items: list[str] = []
    body_ordinals: list[int] = []
    for src in guessed_srcs:
        image = by_name.get(Path(src).name)
        if image is None:
            continue
        if image.is_lead:
            items.append(_lead_label(image))
        else:
            body_ordinals.append(ordinals[Path(src).name])
    if body_ordinals:
        items.append(_condensed_ordinals(body_ordinals))
    return items


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


def _order_images(
    images: list[Image], lead_srcs: list[str], body_srcs: list[str]
) -> list[Image]:
    """Return *images* ordered by document position: lead images in
    encounter order, then in-body images in body order, then any
    unreferenced extracted media in their original order.
    """
    by_name = {Path(image.media_filename).name: image for image in images}
    ordered: list[Image] = []
    used: set[str] = set()
    for src in (*lead_srcs, *body_srcs):
        name = Path(src).name
        image = by_name.get(name)
        if image is not None and name not in used:
            ordered.append(image)
            used.add(name)
    ordered.extend(
        image for image in images if Path(image.media_filename).name not in used
    )
    return ordered


def _read_created_date(src: Path) -> str:
    """Return the document's creation timestamp (``dcterms:created`` in
    ``docProps/core.xml``) normalized to ``YYYY-MM-DD HH:MM:SS``, or ``""``
    when the part or element is absent or unreadable.
    """
    try:
        with zipfile.ZipFile(src) as package, package.open("docProps/core.xml") as part:
            root = ElementTree.parse(part).getroot()
    except (
        OSError,
        KeyError,
        ValueError,
        zipfile.BadZipFile,
        ElementTree.ParseError,
    ):
        return ""
    created = root.find(_CORE_CREATED_TAG)
    if created is None or not (text := (created.text or "").strip()):
        return ""
    try:
        return datetime.fromisoformat(text).strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return ""


def _extract_author(soup: BeautifulSoup) -> tuple[str, bool]:
    """Return ``(author, needs_review)`` from the ``data-custom-style="Autor"``
    elements, removing them from *soup*.

    The last element in document order supplies the author; a leading
    ``Autor:`` label is stripped. *needs_review* is True when the author is
    missing (no element, or empty after stripping) or multiple "Autor"
    lines exist (last used); both map to the single ``Autor`` note item.
    """
    elements = soup.find_all(None, attrs={"data-custom-style": _AUTOR_STYLE})
    if not elements:
        return "", True
    author = _AUTOR_LABEL_RE.sub("", elements[-1].get_text()).strip()
    for element in elements:
        element.decompose()
    if not author:
        return "", True
    if len(elements) > 1:
        return author, True
    return author, False


class DocxConverter(AbstractConverter):
    def convert(self, src: Path) -> Article:
        """Convert a .docx file to an article with raw HTML output."""
        media_dir = tempfile.mkdtemp(prefix="media-")
        try:
            fallback_title = src.stem
            note_builder = NoteBuilder()
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
            captions: dict[str, str] = {}
            guessed_srcs: list[str] = []
            if heading:
                title: str = heading.get_text()
                # Images in document order before the first heading are lead
                # images: record their src and remove their top-level block,
                # plus the caption line below it, from the body.
                for el in soup.find_all(True):
                    if el is heading:
                        break
                    if el.parent is None:
                        continue  # detached by an earlier decompose
                    if el.name == "img":
                        img_src = el.get("src")
                        # Must stay after the src read: attrs vanish on decompose.
                        if img_src:
                            img_src = str(img_src)
                            lead_srcs.append(img_src)
                            block = _top_level_block(el, soup)
                            caption = _next_block_sibling(block)
                            if _is_caption_candidate(caption):
                                captions[img_src] = caption.get_text().strip()
                                if caption.get("data-custom-style") != _CAPTION_STYLE:
                                    guessed_srcs.append(img_src)
                                caption.decompose()
                            block.decompose()
                heading.decompose()
            else:
                # No heading: the title fell back to the source file name,
                # which the publisher must verify.
                title = fallback_title
                note_builder.add(NoteItem.TITLE)

            # In-body images with a caption line directly below are rewritten
            # in place as <figure> with a <figcaption>; the caption text is
            # captured the same way as for lead images.
            for img in soup.find_all("img"):
                block = _top_level_block(img, soup)
                if len(block.find_all("img")) > 1:
                    # Shared block: left untouched so no image is lost.
                    continue
                caption = _next_block_sibling(block)
                if not _is_caption_candidate(caption):
                    continue
                img_src = img.get("src")
                if not img_src:
                    continue
                img_src = str(img_src)
                styled = caption.get("data-custom-style") == _CAPTION_STYLE
                text = caption.get_text().strip()
                figure = soup.new_tag("figure")
                block.insert_after(figure)
                figure.append(img.extract())
                figcaption = soup.new_tag("figcaption")
                figcaption.string = text
                figure.append(figcaption)
                block.decompose()
                caption.decompose()
                captions[img_src] = text
                if not styled:
                    guessed_srcs.append(img_src)

            images: list[Image] = []
            media_path = Path(media_dir)
            if media_path.exists():
                for file_path in media_path.glob("**/*"):
                    if file_path.is_file():
                        media_filename = str(file_path.relative_to(media_path))
                        data = file_path.read_bytes()
                        images.append(Image(media_filename=media_filename, data=data))

            _flag_lead_images(images, lead_srcs)
            _apply_image_captions(images, captions)
            body_srcs = [
                str(img.get("src")) for img in soup.find_all("img") if img.get("src")
            ]
            images = _order_images(images, lead_srcs, body_srcs)

            # The "Autor" styled line carries the author: take the last
            # occurrence, strip an optional "Autor:" label, and remove the
            # line from the body (after lead processing, so an "Autor"-styled
            # lead-image paragraph is not mistaken for the byline).
            author, author_needs_review = _extract_author(soup)
            if author_needs_review:
                note_builder.add(NoteItem.AUTHOR)
            created_date = _read_created_date(src)
            if not created_date:
                note_builder.add(NoteItem.CREATED_DATE)
            for item in _guessed_caption_items(images, guessed_srcs):
                note_builder.add_image_ref(item)
            note = note_builder.build()

            return Article(
                source_file=src,
                title=title,
                slug=slugify(fallback_title),
                body=str(soup),
                created_date=created_date,
                note=note,
                images=images,
                created_by_alias=author,
            )
        except (OSError, ValueError, RuntimeError) as exc:
            raise RuntimeError(f"conversion of {src.name} failed: {exc}") from exc
        finally:
            shutil.rmtree(media_dir, ignore_errors=True)
