"""Command-line entry point: publish one .docx document to Joomla.

Installed as the ``docxwire`` console command; :func:`main` is also
callable in-process with an explicit argument list.

Exit codes: 0 success, 1 operational failure (settings, conversion, or
API), 2 usage error (argparse default).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from docxwire.joomla.client import JoomlaApiError
from docxwire.publish import publish_article
from docxwire.settings import SettingsError, load_settings

__all__ = ["main"]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="docxwire",
        description="Publish a .docx document to the configured Joomla site.",
    )
    parser.add_argument("docx", help="path to the .docx file to publish")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the single-document publishing flow; returns the exit code."""
    args = _build_parser().parse_args(argv)
    docx_path = Path(args.docx)
    if not docx_path.is_file():
        _fail(f"{docx_path} not found; pass a path to an existing .docx file")
        return 1
    try:
        settings = load_settings()
        created = publish_article(docx_path, settings)
    # ValueError: the payload build (e.g. a body image reference that
    # matches no uploaded image).
    except (SettingsError, RuntimeError, JoomlaApiError, ValueError) as exc:
        _fail(str(exc))
        return 1
    attributes = created.get("attributes", {})
    print(f"Created draft article {created['id']}: {attributes.get('title', '')}")
    note = attributes.get("note", "")
    print(note if note else "Nothing to review.")
    return 0


def _fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
