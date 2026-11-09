from __future__ import annotations

import pytest

from docxwire.converter.base import NoteBuilder, NoteItem, slug_date, slugify


class TestNoteBuilder:
    def test_empty_builder_yields_empty_note(self) -> None:
        assert NoteBuilder().build() == ""

    def test_single_item_gets_pruefe_prefix(self) -> None:
        builder = NoteBuilder()
        builder.add(NoteItem.AUTHOR)
        assert builder.build() == "Prüfe: Autor"

    def test_repeated_item_is_listed_once(self) -> None:
        builder = NoteBuilder()
        builder.add(NoteItem.AUTHOR)
        builder.add(NoteItem.AUTHOR)
        assert builder.build() == "Prüfe: Autor"

    def test_repeated_image_reference_is_listed_once(self) -> None:
        builder = NoteBuilder()
        builder.add_image_ref("Titelbild")
        builder.add_image_ref("Titelbild")
        assert builder.build() == "Prüfe: Titelbild"

    def test_items_render_in_fixed_order_independent_of_insertion(self) -> None:
        builder = NoteBuilder()
        builder.add(NoteItem.CREATED_DATE)
        builder.add_image_ref("1. & 2. Bild")
        builder.add(NoteItem.AUTHOR)
        builder.add(NoteItem.TITLE)
        assert builder.build() == "Prüfe: Titel, Autor, Erstellungsdatum, 1. & 2. Bild"


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


class TestSlugDate:
    @pytest.mark.parametrize(
        "slug, expected",
        [
            ("adams-acht-2026-09", "2026/09"),
            ("ruderkurs-2025-04", "2025/04"),
            ("regatta", ""),
            ("regatta-2026-03-15", ""),
        ],
    )
    def test_extracts_trailing_date_suffix(self, slug: str, expected: str) -> None:
        assert slug_date(slug) == expected
