"""The two ports the commands talk through. Real adapters (gspread, AnkiConnect) and
in-memory test fakes both implement them. Keep them small; add methods as commands need them."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Note:
    """One Note of the `Sentences` note type."""

    english: str
    russian: str
    comment: str


class SheetPort(Protocol):
    """The "phrases" tab."""

    def read_all(self) -> list[list[str]]:
        """Every row of the tab as cell strings, header row first (index 0 = sheet row 1).
        Rows may be ragged: trailing empty cells can be missing."""
        ...

    def update_cells(self, row_number: int, values: dict[int, str]) -> None:
        """Set cells of one sheet row (1-based; the header is row 1), keyed by 0-based
        column index. Other cells of the row are left as they are."""
        ...


class AnkiPort(Protocol):
    """The `Sentenses` deck in the running Anki, spoken to in AnkiConnect's terms. Note fields are keyed by
    their lowercase names: "english", "russian", "comment". Field values are Anki's stored HTML."""

    def find_notes(self, query: str) -> list[int]:
        """Ids of the Notes matching an Anki search query, e.g.
        `"deck:Sentenses" "russian:*старшая*"` (space-separated terms are ANDed)."""
        ...

    def notes_info(self, ids: list[int]) -> list[dict]:
        """For each known id, {"id", "english", "russian", "comment"}. Unknown ids are left out."""
        ...

    def add_note(self, english: str, russian: str, comment: str) -> int:
        """Add one Note of type `Sentences` to the deck, no tags; return its id."""
        ...

    def update_note(self, note_id: int, fields: dict[str, str]) -> None:
        """Set the given fields of an existing Note; other fields are left as they are."""
        ...

    def ping(self) -> bool:
        """Whether Anki is answering right now. Cheap; must not raise when Anki is down."""
        ...

    def sync(self) -> None:
        """Ask Anki to run its own sync (to AnkiWeb)."""
        ...
