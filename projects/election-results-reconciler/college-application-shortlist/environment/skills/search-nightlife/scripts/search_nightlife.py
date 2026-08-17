"""Stub utility for nightlife data (distractor skill)."""

from __future__ import annotations


class Nightlife:
    """Nightlife lookup stub — no bundled data."""

    def __init__(self) -> None:
        print("Nightlife loaded.")

    def run(self, city: str = "") -> str:
        return "No nightlife data is available in the bundled dataset."
