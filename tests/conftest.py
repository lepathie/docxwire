from __future__ import annotations

from pathlib import Path

import pytest

DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def ruderkurs_doc() -> Path:
    """Clean document, 100% template adherence, single image before body."""
    return DATA_DIR / "2025.04 Ruderkurs.docx"
