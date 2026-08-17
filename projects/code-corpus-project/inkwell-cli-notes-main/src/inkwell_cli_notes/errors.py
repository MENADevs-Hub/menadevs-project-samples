"""Shared exception types for CLI workflows."""


class InkwellError(Exception):
    """Base class for user-facing application errors."""


class StorageError(InkwellError):
    """Raised when the on-disk note store cannot be read or written."""


class NoteNotFoundError(StorageError):
    """Raised when a note reference cannot be resolved."""


class AmbiguousNoteError(StorageError):
    """Raised when a note reference matches more than one note."""


class InvalidNoteError(StorageError):
    """Raised when a note file fails validation."""


class EditorError(InkwellError):
    """Raised when a note cannot be opened or saved through an editor."""
