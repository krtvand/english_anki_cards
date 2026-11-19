"""The command layer: one function per CLI command, taking the ports and returning a
JSON-ready dict. This is the test seam."""

from anki_notes import constants as c
from anki_notes.html import comment_to_html, escape_text
from anki_notes.ports import AnkiPort, Note, SheetPort
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


def sync(anki: AnkiPort) -> dict:
    """Ask Anki to sync, so new Notes reach the phone."""
    anki.sync()
    return {"synced": True}


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


def add(sheet: SheetPort, anki: AnkiPort, row: int, english: str, russian: str, notes: list[Note]) -> dict:
    """Put the approved Note into the deck (unless a Note with the same russian is already
    there), then write it back to the referenced Row and mark the Row Added (`1`)."""
    if len(notes) != 1:
        raise CommandError("add takes exactly one Note")
    cols, target = locate_row(sheet, row, english, russian)
    note = notes[0]
    note_id, added = _ensure_in_deck(anki, note)
    write_note_to_row(sheet, cols, target.number, note)
    return {"row": target.number, "anki": c.ADDED, "notes": [{"id": note_id, "added": added}]}


def _ensure_in_deck(anki: AnkiPort, note: Note) -> tuple[int, bool]:
    """The id of the deck's Note with exactly this russian, adding the Note if there is none.
    Returns (id, whether it was added now). This is what makes re-running `add` safe."""
    russian = escape_text(note.russian)
    candidates = anki.find_notes(f'deck:{c.DECK} "russian:{_anki_search_escape(russian)}"')
    for info in anki.notes_info(candidates) if candidates else []:
        if info["russian"] == russian:
            return info["id"], False
    return anki.add_note(escape_text(note.english), russian, comment_to_html(note.comment)), True


def _anki_search_escape(text: str) -> str:
    """Make `text` match literally inside a quoted Anki field search."""
    for ch in ("\\", '"', "*", "_"):
        text = text.replace(ch, "\\" + ch)
    return text


def write_note_to_row(sheet: SheetPort, cols: Columns, row_number: int, note: Note) -> None:
    """Write a Note's plain-text english/russian/comment to a sheet row and mark it Added."""
    sheet.update_cells(
        row_number,
        {
            cols.english: note.english,
            cols.russian: note.russian,
            cols.comment: note.comment,
            cols.anki: c.ADDED,
        },
    )


def discard(sheet: SheetPort, anki: AnkiPort, row: int, english: str, russian: str) -> dict:
    """Mark the referenced Row Discarded (`-`). The deck is not touched."""
    cols, target = locate_row(sheet, row, english, russian)
    sheet.update_cells(target.number, {cols.anki: c.DISCARDED})
    return {"row": target.number, "anki": c.DISCARDED}
