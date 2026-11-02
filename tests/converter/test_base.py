from __future__ import annotations

import pytest

from docxwire.converter.base import slugify


class TestSlugify:
    @pytest.mark.parametrize(
        "filename, expected",
        [
            ("2025.04 Ruderkurs", "ruderkurs-2025-04"),
            ("2024-12_Year Review", "year-review-2024-12"),
            ("My---Article   Title", "my-article-title"),
            ("simple", "simple"),
            ("  spaced  title  ", "spaced-title"),
        ],
    )
    def test_formats_correctly(self, filename: str, expected: str) -> None:
        assert slugify(filename) == expected
