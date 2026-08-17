"""Ranking helpers for note search."""

from __future__ import annotations

import re
from collections.abc import Sequence

from inkwell_cli_notes.models import Note


def search_notes(
    notes: Sequence[Note],
    query: str,
    *,
    limit: int | None = None,
) -> list[tuple[Note, float]]:
    """Return ranked search results for a query string."""

    tokens = _tokenize(query)
    if not tokens:
        return []

    # Scoring happens in two passes so we can keep the weight calculation easy
    # to inspect and still filter out non-matches before sorting.
    scored = [(note, _score_note(note, tokens)) for note in notes]
    ranked = sorted(
        (item for item in scored if item[1] > 0),
        key=lambda item: item[1],
        reverse=True,
    )
    if limit is not None:
        return ranked[:limit]
    return ranked


def _tokenize(query: str) -> list[str]:
    # Search treats repeated whitespace as insignificant and stays case
    # insensitive so pasted terminal snippets behave like ordinary text.
    return [token for token in re.split(r"\s+", query.lower().strip()) if token]


def _score_note(note: Note, tokens: Sequence[str]) -> float:
    haystack_title = note.metadata.title.lower()
    haystack_body = note.body.lower()
    haystack_tags = " ".join(note.metadata.tags).lower()
    haystack_notebook = note.metadata.notebook.lower()
    score = 0.0
    # Full-title phrase matches get a large bonus because they usually reflect
    # deliberate note lookup rather than exploratory keyword search.
    if " ".join(tokens) in haystack_title:
        score += 25.0
    for token in tokens:
        # Title and tag matches are weighted above body matches so results feel
        # closer to how people organize notes for later retrieval.
        score += _score_token(token, haystack_title, 10.0)
        score += _score_token(token, haystack_tags, 8.0)
        score += _score_token(token, haystack_notebook, 6.0)
        score += _score_token(token, haystack_body, 1.0)
    # Pinned notes get a slight bump, while archived notes take a small
    # penalty, because both states are relevance hints rather than hard rules.
    if note.metadata.pinned:
        score += 1.5
    if note.metadata.archived:
        score -= 2.0
    return score


def _score_token(token: str, haystack: str, weight: float) -> float:
    occurrences = haystack.count(token)
    return occurrences * weight
