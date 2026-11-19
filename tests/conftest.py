import io
import json

import pytest

from fakes import FakeAnki, FakeClock, FakeLauncher, FakeSheet

from anki_notes.cli import run_command


def run(argv, sheet, anki, *, launch_anki=None, clock=None, stdin=None, err=None):
    """Run one CLI command against the fakes; return (exit code, parsed JSON output).
    Never launches the real Anki app or really sleeps: launcher and clock default to fakes."""
    out = io.StringIO()
    code = run_command(
        argv,
        sheet=sheet,
        anki=anki,
        out=out,
        launch_anki=launch_anki or FakeLauncher(),
        clock=clock or FakeClock(),
        stdin=io.StringIO(stdin) if isinstance(stdin, str) else stdin,
        err=err if err is not None else io.StringIO(),
    )
    return code, json.loads(out.getvalue())


@pytest.fixture
def make_sheet():
    def make(*grid):
        return FakeSheet([list(row) for row in grid])

    return make


@pytest.fixture
def anki():
    return FakeAnki()
