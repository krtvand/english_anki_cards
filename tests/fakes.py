"""In-memory stand-ins for the Sheet and Anki ports. Tests read and set their state directly."""

from anki_notes.ports import Note


class FakeSheet:
    """The "phrases" tab as a grid of cells; grid[0] is the header row (sheet row 1)."""

    def __init__(self, grid: list[list[str]]):
        self.grid = grid

    def read_all(self) -> list[list[str]]:
        return [list(row) for row in self.grid]


class FakeAnki:
    """The deck as a dict of Notes keyed by note id."""

    def __init__(self, notes: dict[int, Note] | None = None):
        self.notes: dict[int, Note] = dict(notes or {})
