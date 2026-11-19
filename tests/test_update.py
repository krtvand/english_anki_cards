import json

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


def test_merge_can_append_to_the_existing_comment_leaving_its_html_untouched(make_sheet):
    anki = FakeAnki({11: Note("I have an older daughter", "У меня есть старшая дочь", "<b>older</b> &amp; elder")})
    sheet = make_sheet(HEADER, ["My eldest daughter", "Моя дочь", "", ""])

    code, _ = run(
        update(2, "My eldest daughter", "Моя дочь", "--note-id", "11", "--append-comment", "**eldest** = of 3+\n<rare>"),
        sheet,
        anki,
    )

    assert code == 0
    assert anki.notes[11].comment == "<b>older</b> &amp; elder<br><br><b>eldest</b> = of 3+<br>&lt;rare&gt;"
    assert sheet.grid[1][3] == "1"


def test_appending_to_an_empty_comment_adds_no_separator(make_sheet):
    anki = FakeAnki({11: Note("I have an older daughter", "У меня есть старшая дочь", "")})
    sheet = make_sheet(HEADER, ["My eldest daughter", "Моя дочь", "", ""])

    run(update(2, "My eldest daughter", "Моя дочь", "--note-id", "11", "--append-comment", "eldest"), sheet, anki)

    assert anki.notes[11].comment == "eldest"


def test_merge_values_can_come_from_stdin_json(make_sheet):
    anki = FakeAnki({11: Note("I have an older daughter", "У меня есть старшая дочь", "old")})
    sheet = make_sheet(HEADER, ["My eldest daughter", "Моя дочь", "", ""])
    fields = {"english": 'I have an "eldest" daughter', "append_comment": "line 'one'\nline two"}

    code, out = run(
        update(2, "My eldest daughter", "Моя дочь", "--note-id", "11", "--fields-json", "-"),
        sheet,
        anki,
        stdin=json.dumps(fields),
    )

    assert code == 0
    assert out == {"row": 2, "anki": "1", "note_id": 11}
    assert anki.notes[11] == Note(
        'I have an "eldest" daughter', "У меня есть старшая дочь", "old<br><br>line 'one'<br>line two"
    )


def test_replacing_and_appending_the_comment_at_once_is_refused(make_sheet):
    anki = FakeAnki({11: Note("I have an older daughter", "У меня есть старшая дочь", "old")})
    sheet = make_sheet(HEADER, ["My eldest daughter", "Моя дочь", "", ""])
    before = [list(r) for r in sheet.grid]

    code, out = run(
        update(2, "My eldest daughter", "Моя дочь", "--note-id", "11", "--new-comment", "a", "--append-comment", "b"),
        sheet,
        anki,
    )

    assert code == 1 and set(out) == {"error"}
    assert anki.notes[11].comment == "old"
    assert sheet.grid == before


def test_malformed_fields_json_is_refused(make_sheet):
    anki = FakeAnki({11: Note("I have an older daughter", "У меня есть старшая дочь", "old")})
    sheet = make_sheet(HEADER, ["My eldest daughter", "Моя дочь", "", ""])
    argv = update(2, "My eldest daughter", "Моя дочь", "--note-id", "11", "--fields-json")

    for bad in ("not json", "[]", '{"english": 1}', '{"title": "x"}'):
        code, out = run([*argv, bad], sheet, anki)
        assert code == 1 and set(out) == {"error"}, bad
    assert anki.notes[11].comment == "old"
