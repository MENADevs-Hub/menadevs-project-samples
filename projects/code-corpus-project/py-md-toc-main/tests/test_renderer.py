"""Renderer tests for nested TOC output."""

from py_md_toc.parser import Heading
from py_md_toc.renderer import build_toc


def test_build_toc_renders_nested_bullets_from_base_level() -> None:
    """Nested headings should become nested bullet list items."""

    headings = [
        Heading(level=2, text="Parent", slug="parent", line=1),
        Heading(level=3, text="Child", slug="child", line=2),
        Heading(level=4, text="Grandchild", slug="grandchild", line=3),
    ]

    assert build_toc(headings) == (
        "- [Parent](#parent)\n"
        "  - [Child](#child)\n"
        "    - [Grandchild](#grandchild)"
    )


def test_build_toc_supports_custom_bullet_and_indent() -> None:
    """Callers should be able to adjust bullet and indentation style."""

    headings = [Heading(level=1, text="Intro", slug="intro", line=1)]

    assert build_toc(headings, bullet="*", indent=4) == "* [Intro](#intro)"


def test_build_toc_returns_empty_string_for_no_headings() -> None:
    """An empty heading list should render to an empty TOC string."""

    assert build_toc([]) == ""
