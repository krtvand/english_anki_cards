"""The command layer: one function per CLI command, taking the ports and returning a
JSON-ready dict. This is the test seam."""

from anki_notes.ports import AnkiPort, SheetPort
from anki_notes.rows import parse_rows


def next_row(sheet: SheetPort, anki: AnkiPort, exclude: frozenset[int] = frozenset()) -> dict:
    """The topmost Pending row whose Row number is not in `exclude` (the session's Skipped Rows)."""
    _, rows = parse_rows(sheet.read_all())
    for row in rows:
        if row.is_pending and row.number not in exclude:
            return {
                "row": row.number,
                "english": row.english,
                "russian": row.russian,
                "comment": row.comment,
            }
    return {"nothing_left": True}
