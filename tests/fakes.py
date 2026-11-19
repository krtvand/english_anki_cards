"""In-memory stand-ins for the Sheet and Anki ports. Tests read and set their state directly."""

from anki_notes.ports import Note


class FakeSheet:
    """The "phrases" tab as a grid of cells; grid[0] is the header row (sheet row 1)."""

    def __init__(self, grid: list[list[str]]):
        self.grid = grid

    def read_all(self) -> list[list[str]]:
        return [list(row) for row in self.grid]

    def update_cells(self, row_number: int, values: dict[int, str]) -> None:
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
