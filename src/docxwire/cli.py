"""Command-line entry point: publish one .docx document to Joomla.

Installed as the ``docxwire`` console command; :func:`main` is also
callable in-process with an explicit argument list.

Exit codes: 0 success, 1 operational failure (settings, conversion, or
API), 2 usage error (argparse default).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from docxwire.joomla.client import JoomlaApiError
from docxwire.publish import publish_article
from docxwire.settings import (
    Settings,
    SettingsError,
    load_settings,
    load_settings_from_env,
)

__all__ = ["main"]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="docxwire",
        description="Publish a .docx document to the configured Joomla site.",
    )
    parser.add_argument("docx", help="path to the .docx file to publish")
    parser.add_argument(
        "--json",
        action="store_true",
        help="write a single JSON object to stdout instead of the text report",
    )
    parser.add_argument(
        "--settings-env",
        action="store_true",
        help="load settings from the DOCXWIRE_JOOMLA_* environment variables "
        "instead of settings.toml",
    )
    return parser


def _load_settings(args: argparse.Namespace) -> Settings:
    """Load settings from the source the flags select.

    ``--settings-env`` selects the ``DOCXWIRE_JOOMLA_*`` environment
    variables; otherwise the ``settings.toml`` in the current working
    directory is used.
    """
    if args.settings_env:
        return load_settings_from_env()
    return load_settings()


def main(argv: list[str] | None = None) -> int:
    """Run the single-document publishing flow; returns the exit code."""
    args = _build_parser().parse_args(argv)
    docx_path = Path(args.docx)
    if not docx_path.is_file():
        _fail(f"{docx_path} not found; pass a path to an existing .docx file")
        return 1
    try:
        settings = _load_settings(args)
        created = publish_article(docx_path, settings)
    # ValueError: the payload build (e.g. a body image reference that
    # matches no uploaded image).
    except (SettingsError, RuntimeError, JoomlaApiError, ValueError) as exc:
        if args.json:
            print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        else:
            _fail(str(exc))
        return 1
    attributes = created.get("attributes", {})
    note = attributes.get("note", "")
    if args.json:
        print(
            json.dumps(
                {
                    "id": created["id"],
                    "title": attributes.get("title", ""),
                    "note": note,
                },
                ensure_ascii=False,
            )
        )
    else:
        print(f"Created draft article {created['id']}: {attributes.get('title', '')}")
        print(note if note else "Nothing to review.")
    return 0


def _fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
