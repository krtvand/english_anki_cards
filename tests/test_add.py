import io
import json

import pytest

from fakes import FakeAnki

from anki_notes.cli import run_command
from anki_notes.ports import Note
from conftest import run

HEADER = ["english", "russian", "comment", "anki"]


def add(row, english, russian, *notes):
    return [
        "add",
        "--row", str(row),
        "--english", english,
        "--russian", russian,
        "--notes-json", json.dumps(list(notes), ensure_ascii=False),
    ]


def note(english, russian, comment=""):
    return {"english": english, "russian": russian, "comment": comment}


def test_approved_note_lands_in_the_deck_and_the_row_is_updated_and_marked_added(make_sheet, anki):
    sheet = make_sheet(
        HEADER,
        ["I have a older daugter", "У меня есть *старшая* дочь", "eldest?", ""],
        ["See you tomorrow", "Увидимся завтра", "", ""],
    )

    code, out = run(
        add(
            2, "I have a older daugter", "У меня есть *старшая* дочь",
            note("I have an older daughter", "У меня есть *старшая* дочь", "Также: eldest"),
        ),
        sheet,
        anki,
    )

    assert code == 0
    assert list(anki.notes.values()) == [
        Note("I have an older daughter", "У меня есть *старшая* дочь", "Также: eldest")
    ]
    assert out == {"row": 2, "anki": "1", "notes": [{"id": next(iter(anki.notes)), "added": True}]}
    assert sheet.grid == [
        HEADER,
        ["I have an older daughter", "У меня есть *старшая* дочь", "Также: eldest", "1"],
        ["See you tomorrow", "Увидимся завтра", "", ""],
    ]


def test_notes_can_come_from_stdin(make_sheet, anki):
    sheet = make_sheet(HEADER, ["It's on me", "Я угощаю", "", ""])
    out = io.StringIO()
    stdin = io.StringIO(json.dumps([note("It's on me", "Я угощаю", "casual")], ensure_ascii=False))

    code = run_command(
        ["add", "--row", "2", "--english", "It's on me", "--russian", "Я угощаю", "--notes-json", "-"],
        sheet=sheet, anki=anki, out=out, stdin=stdin,
    )

    assert code == 0
    assert list(anki.notes.values()) == [Note("It's on me", "Я угощаю", "casual")]
    assert sheet.grid[1][3] == "1"


def test_malformed_notes_json_is_refused_and_nothing_is_written(make_sheet, anki):
    sheet = make_sheet(HEADER, ["It's on me", "Я угощаю", "", ""])
    argv = ["add", "--row", "2", "--english", "It's on me", "--russian", "Я угощаю", "--notes-json"]

    for bad in ("not json", "[]", '[{"english": 1}]'):
        code, out = run([*argv, bad], sheet, anki)
        assert code == 1 and set(out) == {"error"}
    assert anki.notes == {}
    assert sheet.grid[1] == ["It's on me", "Я угощаю", "", ""]


def added_comment(make_sheet, anki, comment, russian="Я *угощаю*"):
    """Run `add` for one Note with this comment; return the Note the deck received."""
    sheet = make_sheet(HEADER, ["It's on me", russian, "", ""])
    code, _ = run(add(2, "It's on me", russian, note("It's on me", russian, comment)), sheet, anki)
    assert code == 0
    (stored,) = anki.notes.values()
    assert sheet.grid[1][2] == comment  # the Sheet keeps the plain text
    return stored


def test_html_special_characters_render_as_text_and_russian_asterisks_stay_literal(make_sheet, anki):
    sheet = make_sheet(HEADER, ["a < b & c", "*а* < б & в", "", ""])

    run(add(2, "a < b & c", "*а* < б & в", note("a < b & c", "*а* < б & в", "x <b>not bold</b> & y")), sheet, anki)

    assert list(anki.notes.values()) == [
        Note("a &lt; b &amp; c", "*а* &lt; б &amp; в", "x &lt;b&gt;not bold&lt;/b&gt; &amp; y")
    ]
    assert sheet.grid[1] == ["a < b & c", "*а* < б & в", "x <b>not bold</b> & y", "1"]


def test_comment_line_breaks_become_br(make_sheet, anki):
    stored = added_comment(make_sheet, anki, "first line\nsecond line\n\nafter a gap")

    assert stored.comment == "first line<br>second line<br><br>after a gap"


def test_comment_bold_and_italic_become_tags(make_sheet, anki):
    stored = added_comment(
        make_sheet, anki, "**It's on me** is casual; *my treat* and _I've got this_ too, snake_case stays"
    )

    assert stored.comment == (
        "<b>It's on me</b> is casual; <i>my treat</i> and <i>I've got this</i> too, snake_case stays"
    )


def test_comment_bullet_lines_become_a_list(make_sheet, anki):
    stored = added_comment(
        make_sheet,
        anki,
        "Alternatives:\n- **my treat**\n* I've got this\n• This one's on me\nAll are casual.",
    )

    assert stored.comment == (
        "Alternatives:"
        "<ul><li><b>my treat</b></li><li>I've got this</li><li>This one's on me</li></ul>"
        "All are casual."
    )


def test_comment_headings_become_heading_tags(make_sheet, anki):
    stored = added_comment(make_sheet, anki, "# Usage\nSay it when paying.\n\n## UK\n*I'll get this*")

    assert stored.comment == "<h1>Usage</h1>Say it when paying.<br><h2>UK</h2><i>I'll get this</i>"


def test_a_row_inserted_above_while_the_session_runs_does_not_make_add_write_the_wrong_row(
    make_sheet, anki
):
    sheet = make_sheet(HEADER, ["See you", "Увидимся", "", ""], ["Take care", "Береги себя", "", ""])
    _, shown = run(["next"], sheet, anki)
    sheet.grid.insert(1, ["Cheers", "Будем", "", ""])  # jotted down on the phone meanwhile

    code, out = run(
        add(shown["row"], shown["english"], shown["russian"], note("See you later", "Увидимся")),
        sheet,
        anki,
    )

    assert code == 0
    assert out["row"] == 3
    assert sheet.grid == [
        HEADER,
        ["Cheers", "Будем", "", ""],
        ["See you later", "Увидимся", "", "1"],
        ["Take care", "Береги себя", "", ""],
    ]


def test_an_ambiguous_row_is_refused_before_anything_is_written(make_sheet, anki):
    sheet = make_sheet(HEADER, ["See you", "Увидимся", "", ""])
    _, shown = run(["next"], sheet, anki)
    sheet.grid.insert(1, ["Cheers", "Будем", "", ""])
    sheet.grid.append(["See you", "Увидимся", "again", ""])
    before = [list(r) for r in sheet.grid]

    code, out = run(
        add(shown["row"], shown["english"], shown["russian"], note("See you later", "Увидимся")),
        sheet,
        anki,
    )

    assert code == 1
    assert set(out) == {"error"}
    assert sheet.grid == before
    assert anki.notes == {}


def test_rerunning_add_after_the_sheet_write_failed_finishes_the_row_without_a_second_note(
    make_sheet, anki
):
    sheet = make_sheet(HEADER, ["It's on me", "Я *угощаю*", "", ""])
    argv = add(2, "It's on me", "Я *угощаю*", note("It's on me", "Я *угощаю*", "Also: my treat"))
    sheet.fail_writes = True  # e.g. the network drops after Anki has the Note

    with pytest.raises(ConnectionError):
        run(argv, sheet, anki)
    assert len(anki.notes) == 1
    assert sheet.grid[1] == ["It's on me", "Я *угощаю*", "", ""]

    sheet.fail_writes = False
    code, out = run(argv, sheet, anki)

    assert code == 0
    assert list(anki.notes.values()) == [Note("It's on me", "Я *угощаю*", "Also: my treat")]
    assert out["notes"] == [{"id": next(iter(anki.notes)), "added": False}]
    assert sheet.grid[1] == ["It's on me", "Я *угощаю*", "Also: my treat", "1"]


def test_a_note_whose_russian_only_resembles_an_existing_one_is_still_added(make_sheet):
    anki = FakeAnki({1: Note("I treat", "Я угощаю", ""), 2: Note("x", "Я *угощаю* вас", "")})
    sheet = make_sheet(HEADER, ["It's on me", "Я *угощаю*", "", ""])

    code, out = run(add(2, "It's on me", "Я *угощаю*", note("It's on me", "Я *угощаю*")), sheet, anki)

    assert code == 0
    assert out["notes"][0]["added"] is True
    assert len(anki.notes) == 3


def test_an_existing_note_with_special_characters_in_its_russian_is_recognised(make_sheet):
    russian = 'Том & "Джерри" \\ *кот*_'
    anki = FakeAnki({7: Note("Tom & Jerry", 'Том &amp; "Джерри" \\ *кот*_', "")})
    sheet = make_sheet(HEADER, ["Tom & Jerry", russian, "", ""])

    code, out = run(add(2, "Tom & Jerry", russian, note("Tom & Jerry", russian)), sheet, anki)

    assert code == 0
    assert out["notes"] == [{"id": 7, "added": False}]
    assert len(anki.notes) == 1
