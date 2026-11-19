from fakes import FakeAnki

from anki_notes.ports import Note
from conftest import run

HEADER = ["english", "russian", "comment", "anki"]


def update(row, english, russian, *extra):
    return ["update", "--row", str(row), "--english", english, "--russian", russian, *extra]


def test_merge_updates_the_existing_note_and_marks_the_row(make_sheet):
    anki = FakeAnki({11: Note("I have an older daughter", "У меня есть старшая дочь", "")})
    sheet = make_sheet(
        HEADER,
        ["My older daughter", "Моя *старшая* дочь", "eldest?", ""],
    )

    code, out = run(
        update(
            2, "My older daughter", "Моя *старшая* дочь",
            "--note-id", "11",
            "--new-english", "I have an eldest daughter",
            "--new-comment", "eldest = the oldest of three or more",
        ),
        sheet,
        anki,
    )

    assert code == 0
    assert out == {"row": 2, "anki": "1", "note_id": 11}
    assert anki.notes == {
        11: Note(
            "I have an eldest daughter",
            "У меня есть старшая дочь",
            "eldest = the oldest of three or more",
        )
    }
    assert sheet.grid == [HEADER, ["My older daughter", "Моя *старшая* дочь", "eldest?", "1"]]


def test_merge_with_only_a_comment_leaves_the_english_alone(make_sheet):
    anki = FakeAnki({11: Note("I have an older daughter", "У меня есть старшая дочь", "old")})
    sheet = make_sheet(HEADER, ["My older daughter", "Моя дочь", "", ""])

    code, _ = run(
        update(2, "My older daughter", "Моя дочь", "--note-id", "11", "--new-comment", "line one\nline two"),
        sheet,
        anki,
    )

    assert code == 0
    note = anki.notes[11]
    assert note.english == "I have an older daughter"
    assert note.comment.startswith("line one") and "<br>" in note.comment
    assert len(anki.notes) == 1


def test_merge_into_an_unknown_note_fails_and_leaves_the_sheet_unchanged(make_sheet):
    anki = FakeAnki({11: Note("I have an older daughter", "У меня есть старшая дочь", "")})
    sheet = make_sheet(HEADER, ["My older daughter", "Моя дочь", "", ""])
    before = [list(r) for r in sheet.grid]

    code, out = run(
        update(2, "My older daughter", "Моя дочь", "--note-id", "99", "--new-english", "x"),
        sheet,
        anki,
    )

    assert code == 1
    assert "99" in out["error"]
    assert sheet.grid == before
    assert anki.notes == {11: Note("I have an older daughter", "У меня есть старшая дочь", "")}


def test_merge_with_nothing_to_change_is_refused(make_sheet):
    anki = FakeAnki({11: Note("I have an older daughter", "У меня есть старшая дочь", "")})
    sheet = make_sheet(HEADER, ["My older daughter", "Моя дочь", "", ""])
    before = [list(r) for r in sheet.grid]

    code, out = run(update(2, "My older daughter", "Моя дочь", "--note-id", "11"), sheet, anki)

    assert code == 1
    assert set(out) == {"error"}
    assert sheet.grid == before
