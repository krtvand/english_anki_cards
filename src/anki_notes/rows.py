"""Reading Rows out of the raw Sheet grid, with columns found by header name."""

from dataclasses import dataclass

from anki_notes import constants as c


@dataclass(frozen=True)
class Row:
    number: int  # sheet row number; the header is row 1
    english: str
    russian: str
    comment: str
    anki: str

    @property
    def is_pending(self) -> bool:
        return self.anki == c.PENDING and bool(self.english or self.russian)


@dataclass(frozen=True)
class Columns:
    """0-based column index of each named header."""

    english: int
    russian: int
    comment: int
    anki: int

    @classmethod
    def from_header(cls, header: list[str]) -> "Columns":
        names = [cell.strip().lower() for cell in header]
        missing = [h for h in (c.ENGLISH, c.RUSSIAN, c.COMMENT, c.ANKI) if h not in names]
        if missing:
            raise ValueError(f"Sheet header is missing column(s): {', '.join(missing)}")
        return cls(
            english=names.index(c.ENGLISH),
            russian=names.index(c.RUSSIAN),
            comment=names.index(c.COMMENT),
            anki=names.index(c.ANKI),
        )


def parse_rows(grid: list[list[str]]) -> tuple[Columns, list[Row]]:
    """Split the grid into its header's Columns and the Rows below it."""
    if not grid:
        raise ValueError("Sheet is empty: no header row")
    cols = Columns.from_header(grid[0])

    def cell(cells: list[str], i: int) -> str:
        return cells[i].strip() if i < len(cells) else ""

    rows = [
        Row(
            number=i + 1,
            english=cell(cells, cols.english),
            russian=cell(cells, cols.russian),
            comment=cell(cells, cols.comment),
            anki=cell(cells, cols.anki),
        )
        for i, cells in enumerate(grid)
        if i > 0
    ]
    return cols, rows
