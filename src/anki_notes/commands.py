"""The command layer: one function per CLI command, taking the ports and returning a
JSON-ready dict. This is the test seam."""

import math
import re

from anki_notes import constants as c
from anki_notes.errors import CommandError
from anki_notes.html import comment_to_html, escape_text
from anki_notes.ports import AnkiPort, Note, SheetPort
from anki_notes.rows import Columns, Row, parse_rows

__all__ = ["CommandError", "add", "discard", "find", "locate_row", "next_row", "sync", "update"]

COMMENT_SEPARATOR = "<br><br>"  # between a Note's existing comment and an appended one


def next_row(sheet: SheetPort, exclude: frozenset[int] = frozenset()) -> dict:
    """The topmost Pending row whose Row number is not in `exclude` (the session's Skipped Rows)."""
    _, rows = parse_rows(sheet.read_all())
    for row in rows:
        if row.is_pending and row.number not in exclude:
            return {
                "row": row.number,
                c.ENGLISH: row.english,
                c.RUSSIAN: row.russian,
                c.COMMENT: row.comment,
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
    at_number = next((r for r in rows if r.number == row), None)
    if at_number is not None and at_number.holds(english, russian):
        return cols, at_number
    found = [r for r in rows if r.holds(english, russian)]
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
    """Put the approved Notes into the deck (each unless a Note with the same russian is
    already there). Each extra Note gets its own Row inserted directly below the referenced
    Row, filled in and marked Added (`1`); then the first Note is written back to the
    referenced Row and that Row is marked Added.

    The source Row is written last, so after any failure it still holds what `next` printed
    and a re-run finds it again; extra Rows already below it are recognised, not repeated."""
    locate_row(sheet, row, english, russian)  # refuse before touching Anki if the Row is gone
    results = []
    for note in notes:
        note_id, added = _ensure_in_deck(anki, note)
        results.append({"id": note_id, "added": added})
    # The phone may have changed the Sheet while Anki was written: find the Row again.
    cols, target = locate_row(sheet, row, english, russian)
    _, rows = parse_rows(sheet.read_all())
    by_number = {r.number: r for r in rows}
    for offset, note in enumerate(notes[1:], start=1):
        number = target.number + offset
        below = by_number.get(number)
        if not (below and below.holds(note.english, note.russian) and below.anki == c.ADDED):
            cells = _added_note_cells(cols, note)
            sheet.insert_row(number, [cells.get(i, "") for i in range(max(cells) + 1)])
    sheet.update_cells(target.number, _added_note_cells(cols, notes[0]))
    return {"row": target.number, "anki": c.ADDED, "notes": results}


def _added_note_cells(cols: Columns, note: Note) -> dict[int, str]:
    """The cells of a sheet row logging this Note (plain text) as Added, by column index."""
    return {cols.english: note.english, cols.russian: note.russian, cols.comment: note.comment, cols.anki: c.ADDED}


def _ensure_in_deck(anki: AnkiPort, note: Note) -> tuple[int, bool]:
    """The id of the deck's Note with exactly this russian (or, when the russian is empty,
    exactly this english), adding the Note if there is none. Returns (id, whether it was
    added now). This is what makes re-running `add` safe."""
    english, russian = escape_text(note.english), escape_text(note.russian)
    field, text = (c.RUSSIAN, russian) if russian.strip() else (c.ENGLISH, english)
    candidates = anki.find_notes(_contains(field, text)) if text.strip() else []
    for info in anki.notes_info(candidates) if candidates else []:
        if info[field] == text:  # the search is "contains"; only an exact match counts
            return info["id"], False
    return anki.add_note(english, russian, comment_to_html(note.comment)), True


def discard(sheet: SheetPort, row: int, english: str, russian: str) -> dict:
    """Mark the referenced Row Discarded (`-`). The deck is not touched."""
    cols, target = locate_row(sheet, row, english, russian)
    sheet.update_cells(target.number, {cols.anki: c.DISCARDED})
    return {"row": target.number, "anki": c.DISCARDED}


_ANKI_SPECIAL = re.compile(r'([\\"*_:])')


def _contains(field: str, text: str) -> str:
    """An Anki search query for deck Notes whose `field` contains `text` (special characters escaped)."""
    escaped = _ANKI_SPECIAL.sub(r"\\\1", text.strip())
    return f'"deck:{c.DECK}" "{field}:*{escaped}*"'


_STOP_WORDS = frozenset(
    "the and are was were you your his her its our their this that these those "
    "for with from not but can will just".split()
)


def significant_words(text: str) -> list[str]:
    """The words of `text` worth searching for: 3+ letters, not a stop word, lowercased, unique."""
    words = [w.lower() for w in re.findall(r"[^\W\d_]+", text)]
    return list(dict.fromkeys(w for w in words if len(w) >= 3 and w not in _STOP_WORDS))


def find(anki: AnkiPort, target: str = "", english: str = "") -> dict:
    """Notes like this Row: those whose russian contains the Target phrase, then those whose
    english contains most of the english's significant words (all of them when there are
    one or two, otherwise at least two thirds), best match first."""
    ids: list[int] = []
    if target.strip():
        ids += anki.find_notes(_contains(c.RUSSIAN, escape_text(target)))
    words = significant_words(english)  # letters only, so nothing to HTML-escape
    if words:
        hits: dict[int, int] = {}
        for word in words:
            for note_id in anki.find_notes(_contains(c.ENGLISH, word)):
                hits[note_id] = hits.get(note_id, 0) + 1
        needed = len(words) if len(words) <= 2 else math.ceil(2 * len(words) / 3)
        ids += sorted((i for i, n in hits.items() if n >= needed), key=lambda i: -hits[i])
    ids = list(dict.fromkeys(ids))
    return {"notes": anki.notes_info(ids) if ids else []}


def update(
    sheet: SheetPort,
    anki: AnkiPort,
    row: int,
    english: str,
    russian: str,
    note_id: int,
    new_english: str = "",
    new_comment: str = "",
    append_comment: str = "",
) -> dict:
    """Merge: change the existing Note, then mark the referenced Row Added (`1`). Adds no
    Note; leaves the Row's text alone.

    `new_english` replaces the english; `new_comment` replaces the whole comment;
    `append_comment` is added after the existing comment (whose HTML is kept as it is).
    Comments are given as plain text/Markdown and converted to HTML."""
    if new_comment.strip() and append_comment.strip():
        raise CommandError("give either a new comment or one to append, not both; nothing was written")
    if not (new_english.strip() or new_comment.strip() or append_comment.strip()):
        raise CommandError("nothing to merge: give a new english and/or a comment")
    cols, target = locate_row(sheet, row, english, russian)
    found = anki.notes_info([note_id])
    if not found:
        raise CommandError(f"no Note with id {note_id} in the deck; nothing was written")
    fields = {}
    if new_english.strip():
        fields[c.ENGLISH] = escape_text(new_english)
    if new_comment.strip():
        fields[c.COMMENT] = comment_to_html(new_comment)
    if append_comment.strip():
        existing = found[0][c.COMMENT]
        addition = comment_to_html(append_comment)
        fields[c.COMMENT] = f"{existing}{COMMENT_SEPARATOR}{addition}" if existing.strip() else addition
    anki.update_note(note_id, fields)
    sheet.update_cells(target.number, {cols.anki: c.ADDED})
    return {"row": target.number, "anki": c.ADDED, "note_id": note_id}
