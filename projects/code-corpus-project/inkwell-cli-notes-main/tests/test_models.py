from inkwell_cli_notes.models import NoteMetadata


def test_note_metadata_normalizes_tags_and_slug() -> None:
    metadata = NoteMetadata.create(
        "  Hello World  ",
        tags=["work", "work", " ideas ", ""],
        notebook=" personal ",
    )

    assert metadata.slug == "hello-world"
    assert metadata.tags == ["work", "ideas"]
    assert metadata.notebook == "personal"
