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


class AnkiPort(Protocol):
    """The `Sentenses` deck. No methods yet: `add`, `find`, `update` and `sync` add theirs."""
