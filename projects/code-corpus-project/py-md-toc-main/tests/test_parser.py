"""Parser tests for Markdown heading extraction."""

from py_md_toc.errors import InvalidHeadingDepthError
from py_md_toc.parser import Heading, parse_headings


def test_parse_headings_extracts_atx_setext_and_skips_code_blocks() -> None:
    """The parser should keep real headings and ignore code-block lookalikes."""

    markdown = """# Intro

## Child *One*

```python
# ignored
```

    ## also ignored

Section with [docs](https://example.com) and `code`
---

Top level with *emphasis*
===

# Intro
"""

    headings = parse_headings(markdown)

    assert headings == [
        Heading(level=1, text="Intro", slug="intro", line=1),
        Heading(level=2, text="Child One", slug="child-one", line=3),
        Heading(
            level=2,
            text="Section with docs and code",
            slug="section-with-docs-and-code",
            line=11,
        ),
        Heading(level=1, text="Top level with emphasis", slug="top-level-with-emphasis", line=14),
        Heading(level=1, text="Intro", slug="intro-1", line=17),
    ]


def test_parse_headings_filters_depth_range() -> None:
    """Depth filters should trim the parsed heading list without reordering it."""

    markdown = """# One
## Two
### Three
"""

    headings = parse_headings(markdown, min_level=2, max_level=3)

    assert headings == [
        Heading(level=2, text="Two", slug="two", line=2),
        Heading(level=3, text="Three", slug="three", line=3),
    ]


def test_parse_headings_rejects_invalid_depth_range() -> None:
    """Invalid heading ranges should fail fast before any parsing work starts."""

    markdown = "# Intro"

    try:
        parse_headings(markdown, min_level=4, max_level=3)
    except InvalidHeadingDepthError as exc:
        assert str(exc) == "min_level cannot be greater than max_level"
    else:  # pragma: no cover - defensive branch
        raise AssertionError("Expected InvalidHeadingDepthError")
