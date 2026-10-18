from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pypandoc

from docxwire.converter.base import AbstractConverter, Article, Image


class DocxConverter(AbstractConverter):
    def convert(self, src: Path) -> Article:
        """Convert a .docx file to an article with raw HTML output."""
        media_dir = tempfile.mkdtemp(prefix="media-")
        try:
            title = src.stem
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

            images = []
            media_path = Path(media_dir)
            if media_path.exists():
                for file_path in media_path.glob("**/*"):
                    if file_path.is_file():
                        media_filename = str(file_path.relative_to(media_path))
                        data = file_path.read_bytes()
                        images.append(Image(media_filename=media_filename, data=data))

            return Article(source_file=src, title=title, body=html, images=images)
        except (OSError, ValueError, RuntimeError) as exc:
            raise RuntimeError(f"conversion of {src.name} failed: {exc}") from exc
        finally:
            shutil.rmtree(media_dir, ignore_errors=True)
