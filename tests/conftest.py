from __future__ import annotations

from pathlib import Path

import pytest

DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def ruderkurs_doc() -> Path:
    """Clean document, 100% template adherence, single image before body."""
    return DATA_DIR / "2025.04 Ruderkurs.docx"


@pytest.fixture(scope="session")
def heineken_doc() -> Path:
    """One image before the heading, five in the body.

    The image paragraphs use non-default paragraph styles: the lead image
    paragraph uses the ``Autor`` style (the same style as the byline at
    the end of the document), and in-body image paragraphs use the
    ``Normal (Web)`` style.
    """
    return DATA_DIR / "2026.03 Heineken Regatta Amsterdam.docx"


@pytest.fixture(scope="session")
def abrudern_doc() -> Path:
    """No image before the heading, two in the body."""
    return DATA_DIR / "2026.10 Abrudern.docx"


@pytest.fixture(scope="session")
def lichterfest_doc() -> Path:
    """Two images before the heading.

    The document contains a third image, ``image2.png``, which is used as
    the fill of a shape rather than as a body image — the body images are
    ``image1``/``image3``.
    """
    return DATA_DIR / "2025.07 Heilbronner Lichterfest 2025.docx"
