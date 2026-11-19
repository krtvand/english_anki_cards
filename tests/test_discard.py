from fakes import FakeAnki

from anki_notes.ports import Note
from conftest import run

HEADER = ["english", "russian", "comment", "anki"]


def discard(row, english, russian):
    return ["discard", "--row", str(row), "--english", english, "--russian", russian]


def test_discard_marks_the_row_and_leaves_the_deck_alone(make_sheet):
    anki = FakeAnki({1: Note("Thank you", "Спасибо", "")})
    sheet = make_sheet(
        HEADER,
        ["old junk", "старьё", "from 2019", ""],
        ["See you tomorrow", "Увидимся завтра", "", ""],
    )

    code, out = run(discard(2, "old junk", "старьё"), sheet, anki)

    assert code == 0
    assert out == {"row": 2, "anki": "-"}
    assert sheet.grid == [
        HEADER,
        ["old junk", "старьё", "from 2019", "-"],
        ["See you tomorrow", "Увидимся завтра", "", ""],
    ]
    assert anki.notes == {1: Note("Thank you", "Спасибо", "")}


def test_a_row_inserted_above_while_the_session_runs_does_not_make_discard_mark_the_wrong_row(
    make_sheet, anki
):
    sheet = make_sheet(
        HEADER,
        ["old junk", "старьё", "", ""],
        ["See you tomorrow", "Увидимся завтра", "", ""],
    )
    _, shown = run(["next"], sheet, anki)
    sheet.grid.insert(1, ["Take care", "Береги себя", "", ""])  # jotted down on the phone meanwhile

    code, out = run(discard(shown["row"], shown["english"], shown["russian"]), sheet, anki)

    assert code == 0
    assert out == {"row": 3, "anki": "-"}
    assert sheet.grid == [
        HEADER,
        ["Take care", "Береги себя", "", ""],
        ["old junk", "старьё", "", "-"],
        ["See you tomorrow", "Увидимся завтра", "", ""],
    ]


def test_two_rows_with_the_same_content_after_a_shift_are_refused(make_sheet, anki):
    sheet = make_sheet(
        HEADER,
        ["old junk", "старьё", "", ""],
        ["See you tomorrow", "Увидимся завтра", "", ""],
    )
    _, shown = run(["next"], sheet, anki)
    sheet.grid.insert(1, ["Take care", "Береги себя", "", ""])
    sheet.grid.insert(4, ["old junk", "старьё", "jotted again", ""])
    before = [list(r) for r in sheet.grid]

    code, out = run(discard(shown["row"], shown["english"], shown["russian"]), sheet, anki)

    assert code == 1
    assert set(out) == {"error"}
    assert "3, 5" in out["error"]
    assert sheet.grid == before


def test_a_row_that_is_gone_is_refused(make_sheet, anki):
    sheet = make_sheet(
        HEADER,
        ["old junk", "старьё", "", ""],
        ["See you tomorrow", "Увидимся завтра", "", ""],
    )
    _, shown = run(["next"], sheet, anki)
    del sheet.grid[1]  # deleted on the phone meanwhile
    before = [list(r) for r in sheet.grid]

    code, out = run(discard(shown["row"], shown["english"], shown["russian"]), sheet, anki)

    assert code == 1
    assert set(out) == {"error"}
    assert sheet.grid == before
