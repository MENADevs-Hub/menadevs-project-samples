"""Stub utility for weather data (distractor skill)."""

from __future__ import annotations


class Weather:
    """Weather lookup stub — no bundled data."""

    def __init__(self) -> None:
        print("Weather loaded.")

    def run(self, city: str = "", state: str = "") -> str:
        return "No weather data is available in the bundled dataset."
