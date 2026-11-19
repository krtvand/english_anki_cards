"""Every failure prints {"error": ...} and exits 1, whatever raised it."""

import io

import pytest

from fakes import FakeAnki

from anki_notes.adapters import AnkiConnectError
from conftest import run

HEADER = ["english", "russian", "comment", "anki"]


@pytest.mark.parametrize(
    "argv",
    [
        ["bogus"],
        [],
        ["add", "--row", "2", "--english", "x"],  # no --notes-json
        ["discard", "--row", "two"],
        ["update", "--row", "2", "--note-id", "11", "--no-such-flag"],
    ],
)
def test_usage_errors_print_a_json_error_and_exit_1(make_sheet, anki, argv):
    code, out = run(argv, make_sheet(HEADER), anki)

    assert code == 1
    assert set(out) == {"error"}


def test_a_sheet_without_the_needed_headers_is_a_json_error(make_sheet, anki):
    code, out = run(["next"], make_sheet(["english", "russian"], ["Hi", "Привет"]), anki)

    assert code == 1
    assert out == {"error": "Sheet header is missing column(s): comment, anki"}


def test_an_empty_sheet_is_a_json_error(make_sheet, anki):
    code, out = run(["next"], make_sheet(), anki)

    assert code == 1
    assert set(out) == {"error"}


def test_an_anki_error_is_a_json_error(make_sheet):
    class Failing(FakeAnki):
        def find_notes(self, query):
            raise AnkiConnectError("AnkiConnect findNotes failed: collection is not available")

    code, out = run(["find", "--target", "дочь"], make_sheet(HEADER), Failing())

    assert code == 1
    assert out == {"error": "AnkiConnect findNotes failed: collection is not available"}


def test_a_dropped_connection_is_a_json_error(make_sheet, anki):
    sheet = make_sheet(HEADER, ["old junk", "старьё", "", ""])
    sheet.fail_writes = True

    code, out = run(["discard", "--row", "2", "--english", "old junk", "--russian", "старьё"], sheet, anki)

    assert code == 1
    assert "write failed" in out["error"]


def test_an_unexpected_bug_is_a_json_error_with_its_traceback_on_stderr(make_sheet):
    class Buggy(FakeAnki):
        def sync(self):
            raise ZeroDivisionError("oops")

    err = io.StringIO()
    code, out = run(["sync"], make_sheet(HEADER), Buggy(), err=err)

    assert code == 1
    assert "ZeroDivisionError" in out["error"] and "oops" in out["error"]
    assert "Traceback" in err.getvalue()
