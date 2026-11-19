"""In-memory stand-ins for the Sheet and Anki ports. Tests read and set their state directly."""

import re
from dataclasses import replace

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


class FakeAnki:
    """The deck as a dict of Notes keyed by note id."""

    def __init__(self, notes: dict[int, Note] | None = None, *, answering: bool = True):
        self.notes: dict[int, Note] = dict(notes or {})
        self.answering = answering  # set False to play "Anki isn't running"
        self.syncs = 0
        self._up_at: tuple["FakeClock", float] | None = None

    def come_up_at(self, clock: "FakeClock", when: float) -> None:
        """Start answering once `clock` reaches `when` (Anki still starting up until then)."""
        self._up_at = (clock, when)

    def ping(self) -> bool:
        if self._up_at and self._up_at[0].now >= self._up_at[1]:
            self.answering = True
        return self.answering

    def sync(self) -> None:
        self.syncs += 1

    def find_notes(self, query: str) -> list[int]:
        """Understands only `deck:<deck> "<field>:<glob>"`: an exact (case-insensitive)
        whole-field match where `*` is any text, `_` one character, and `\\` escapes."""
        m = re.fullmatch(r'deck:(\S+) "(\w+):((?:[^"\\]|\\.)*)"', query)
        if m is None:
            raise ValueError(f"FakeAnki does not understand the query {query!r}")
        deck, field, glob = m.groups()
        if deck != c.DECK:
            return []
        pattern = re.compile(_glob_to_regex(glob), re.IGNORECASE | re.DOTALL)
        return [i for i, n in self.notes.items() if pattern.fullmatch(getattr(n, field))]

    def notes_info(self, ids: list[int]) -> list[dict]:
        return [
            {"id": i, "english": n.english, "russian": n.russian, "comment": n.comment}
            for i, n in ((i, self.notes[i]) for i in ids)
        ]

    def add_note(self, english: str, russian: str, comment: str) -> int:
        note_id = max(self.notes, default=1_700_000_000_000) + 1
        self.notes[note_id] = Note(english, russian, comment)
        return note_id

    def update_note(self, note_id: int, fields: dict[str, str]) -> None:
        self.notes[note_id] = replace(self.notes[note_id], **fields)


def _glob_to_regex(glob: str) -> str:
    out, i = [], 0
    while i < len(glob):
        ch = glob[i]
        if ch == "\\" and i + 1 < len(glob):
            out.append(re.escape(glob[i + 1]))
            i += 2
            continue
        out.append(".*" if ch == "*" else "." if ch == "_" else re.escape(ch))
        i += 1
    return "".join(out)


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
