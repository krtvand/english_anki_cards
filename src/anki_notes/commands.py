"""The command layer: one function per CLI command, taking the ports and returning a
JSON-ready dict. This is the test seam."""

from anki_notes import constants as c
from anki_notes.ports import AnkiPort, SheetPort
from anki_notes.rows import Columns, Row, parse_rows


class CommandError(Exception):
    """A command refused or failed; the CLI prints {"error": message} and exits 1."""


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


def locate_row(sheet: SheetPort, row: int, english: str, russian: str) -> tuple[Columns, Row]:
    """Find the Row a write command refers to: the Row number and the english/russian that
    `next` printed. The Row number wins if its english/russian still match; otherwise the one
    Row with exactly that english and russian."""
    cols, rows = parse_rows(sheet.read_all())

    def matches(r: Row) -> bool:
        return r.english == english.strip() and r.russian == russian.strip()

    at_number = next((r for r in rows if r.number == row), None)
    if at_number is not None and matches(at_number):
        return cols, at_number
    found = [r for r in rows if matches(r)]
    if not found:
        raise CommandError(
            f"Row {row} no longer holds this english/russian and no other Row does; "
            "it may have been edited or deleted, so nothing was written"
        )
    if len(found) > 1:
        numbers = ", ".join(str(r.number) for r in found)
        raise CommandError(
            f"Row {row} no longer holds this english/russian, and several Rows do "
            f"({numbers}); not sure which one is meant, so nothing was written"
        )
    return cols, found[0]


def discard(sheet: SheetPort, anki: AnkiPort, row: int, english: str, russian: str) -> dict:
    """Mark the referenced Row Discarded (`-`). The deck is not touched."""
    cols, target = locate_row(sheet, row, english, russian)
    sheet.update_cells(target.number, {cols.anki: c.DISCARDED})
    return {"row": target.number, "anki": c.DISCARDED}
