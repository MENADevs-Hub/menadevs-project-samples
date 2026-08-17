"""Validated note data models."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from inkwell_cli_notes.utils import generate_note_id, slugify, unique_items, utc_now


class NoteMetadata(BaseModel):
    """Metadata stored in the Markdown front matter for each note."""

    model_config = ConfigDict(frozen=True, populate_by_name=True, extra="forbid")

    note_id: str = Field(alias="id")
    title: str
    slug: str
    tags: list[str] = Field(default_factory=list)
    notebook: str = "default"
    created_at: datetime
    updated_at: datetime
    archived: bool = False
    pinned: bool = False

    @field_validator("title", "slug", "notebook")
    @classmethod
    def _strip_text(cls, value: str) -> str:
        # Front matter is user-editable text, so trimming happens before we
        # enforce non-empty values for the canonical fields.
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("value must not be empty")
        return cleaned

    @field_validator("tags")
    @classmethod
    def _normalize_tags(cls, values: list[str]) -> list[str]:
        # Tags are normalized here so callers can pass rough input and still
        # end up with stable ordering and duplicate-free metadata.
        cleaned = [value.strip() for value in values if value.strip()]
        return unique_items(cleaned)

    @model_validator(mode="after")
    def _validate_slug(self) -> NoteMetadata:
        # Slug validation keeps title-derived filenames deterministic even when
        # notes are edited outside the CLI.
        if self.slug != slugify(self.title):
            raise ValueError("slug must match the title")
        return self

    @classmethod
    def create(
        cls,
        title: str,
        *,
        tags: Iterable[str] = (),
        notebook: str = "default",
        pinned: bool = False,
        archived: bool = False,
        note_id: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> NoteMetadata:
        """Create a validated metadata record with stable defaults."""

        # A single timestamp source keeps created/updated defaults aligned on
        # first write and avoids tiny drift between adjacent field assignments.
        now = utc_now()
        return cls(
            id=note_id or generate_note_id(),
            title=title.strip(),
            slug=slugify(title),
            tags=list(tags),
            notebook=notebook,
            created_at=created_at or now,
            updated_at=updated_at or now,
            archived=archived,
            pinned=pinned,
        )

    def with_changes(
        self,
        *,
        title: str | None = None,
        tags: Iterable[str] | None = None,
        notebook: str | None = None,
        pinned: bool | None = None,
        archived: bool | None = None,
        updated_at: datetime | None = None,
    ) -> NoteMetadata:
        """Return a copy with selected fields updated."""

        changes: dict[str, object] = {}
        if title is not None:
            # Title edits also rewrite the slug because the filename contract is
            # intentionally derived from the user-visible title.
            changes["title"] = title.strip()
            changes["slug"] = slugify(title)
        if tags is not None:
            changes["tags"] = list(tags)
        if notebook is not None:
            changes["notebook"] = notebook.strip()
        if pinned is not None:
            changes["pinned"] = pinned
        if archived is not None:
            changes["archived"] = archived
        changes["updated_at"] = updated_at or utc_now()
        data = self.model_dump(by_alias=True, mode="python")
        data.update(changes)
        return self.__class__.model_validate(data)


@dataclass(frozen=True, slots=True)
class Note:
    """A note file together with its parsed metadata."""

    metadata: NoteMetadata
    body: str
    path: Path

    @property
    def note_id(self) -> str:
        return self.metadata.note_id

    @property
    def slug(self) -> str:
        return self.metadata.slug

    def with_metadata(self, metadata: NoteMetadata) -> Note:
        """Return a note with replaced metadata."""

        return replace(self, metadata=metadata)

    def with_body(self, body: str) -> Note:
        """Return a note with replaced body content."""

        return replace(self, body=body)
