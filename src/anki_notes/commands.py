"""The command layer: one function per CLI command, taking the ports and returning a
JSON-ready dict. This is the test seam."""

import re

from anki_notes import constants as c
from anki_notes.html import comment_to_html, escape_text
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


def discard(sheet: SheetPort, anki: AnkiPort, row: int, english: str, russian: str) -> dict:
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
        ids += anki.find_notes(_contains("russian", target))
    words = significant_words(english)
    if words:
        hits: dict[int, int] = {}
        for word in words:
            for note_id in anki.find_notes(_contains("english", word)):
                hits[note_id] = hits.get(note_id, 0) + 1
        needed = len(words) if len(words) <= 2 else -(-2 * len(words) // 3)
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
) -> dict:
    """Merge: set the existing Note's english and/or comment (comment converted to HTML),
    then mark the referenced Row Added (`1`). Adds no Note; leaves the Row's text alone."""
    fields = {}
    if new_english.strip():
        fields["english"] = escape_text(new_english)
    if new_comment.strip():
        fields["comment"] = comment_to_html(new_comment)
    if not fields:
        raise CommandError("nothing to merge: give a new english and/or comment")
    cols, target = locate_row(sheet, row, english, russian)
    if not anki.notes_info([note_id]):
        raise CommandError(f"no Note with id {note_id} in the deck; nothing was written")
    anki.update_note(note_id, fields)
    sheet.update_cells(target.number, {cols.anki: c.ADDED})
    return {"row": target.number, "anki": c.ADDED, "note_id": note_id}
