"""In-memory stand-ins for the Sheet and Anki ports. Tests read and set their state directly."""

import dataclasses
import re

from anki_notes import constants as c
from anki_notes.ports import Note


class FakeSheet:
    """The "phrases" tab as a grid of cells; grid[0] is the header row (sheet row 1)."""

    def __init__(self, grid: list[list[str]]):
        self.grid = grid
        self.fail_writes = False  # set True to make every write raise, as a dropped connection would

    def read_all(self) -> list[list[str]]:
        return [list(row) for row in self.grid]

    def update_cells(self, row_number: int, values: dict[int, str]) -> None:
        if self.fail_writes:
            raise ConnectionError("FakeSheet: write failed")
        while len(self.grid) < row_number:
            self.grid.append([])
        cells = self.grid[row_number - 1]
        for index, value in values.items():
            cells.extend([""] * (index + 1 - len(cells)))
            cells[index] = value


_TERM = re.compile(r'"((?:[^"\\]|\\.)*)"|(\S+)')
_UNESCAPED_COLON = re.compile(r"(?<!\\):")


class FakeAnki:
    """The deck as a dict of Notes keyed by note id.

    `find_notes` understands only the query shapes the commands emit: space-separated
    (optionally double-quoted) terms, ANDed, each either `deck:NAME` or `field:*text*`
    (case-insensitive "field contains text", with backslash-escaped special characters)."""

    def __init__(self, notes: dict[int, Note] | None = None, *, answering: bool = True):
        self.notes: dict[int, Note] = dict(notes or {})
        self.answering = answering  # set False to play "Anki isn't running"
        self.syncs = 0
        self._up_at: tuple["FakeClock", float] | None = None

    def find_notes(self, query: str) -> list[int]:
        terms = [quoted if quoted is not None else bare for quoted, bare in _TERM.findall(query)]
        return [note_id for note_id, note in self.notes.items() if all(_matches(t, note) for t in terms)]

    def notes_info(self, ids: list[int]) -> list[dict]:
        return [
            {"id": i, **dataclasses.asdict(self.notes[i])} for i in ids if i in self.notes
        ]

    def add_note(self, english: str, russian: str, comment: str) -> int:
        note_id = max(self.notes, default=1000) + 1
        self.notes[note_id] = Note(english, russian, comment)
        return note_id

    def update_note(self, note_id: int, fields: dict[str, str]) -> None:
        if note_id not in self.notes:
            raise KeyError(note_id)
        self.notes[note_id] = dataclasses.replace(self.notes[note_id], **fields)

    def come_up_at(self, clock: "FakeClock", when: float) -> None:
        """Start answering once `clock` reaches `when` (Anki still starting up until then)."""
        self._up_at = (clock, when)

    def ping(self) -> bool:
        if self._up_at and self._up_at[0].now >= self._up_at[1]:
            self.answering = True
        return self.answering

    def sync(self) -> None:
        self.syncs += 1


def _matches(term: str, note: Note) -> bool:
    field, pattern = _UNESCAPED_COLON.split(term.replace('\\"', '"'), maxsplit=1)
    if field == "deck":
        return pattern == c.DECK
    if not (pattern.startswith("*") and pattern.endswith("*")):
        raise ValueError(f"FakeAnki only understands field:*text* terms, got {term!r}")
    text = re.sub(r"\\(.)", r"\1", pattern[1:-1])
    return text.casefold() in getattr(note, field).casefold()


class FakeClock:
    """Time that only moves when someone sleeps, so polling tests run instantly."""

    def __init__(self):
        self.now = 0.0

    def time(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


class FakeLauncher:
    """Stands in for `open -a Anki`. Counts launches and runs `on_launch` (e.g. bring a FakeAnki up)."""

    def __init__(self, on_launch=None):
        self.launches = 0
        self._on_launch = on_launch

    def __call__(self) -> None:
        self.launches += 1
        if self._on_launch:
            self._on_launch()
