import io
import json

import pytest

from fakes import FakeAnki, FakeSheet

from anki_notes.cli import run_command


def run(argv, sheet, anki):
    """Run one CLI command against the fakes; return (exit code, parsed JSON output)."""
    out = io.StringIO()
    code = run_command(argv, sheet=sheet, anki=anki, out=out)
    return code, json.loads(out.getvalue())


@pytest.fixture
def make_sheet():
    def make(*grid):
        return FakeSheet([list(row) for row in grid])

    return make


@pytest.fixture
def anki():
    return FakeAnki()
