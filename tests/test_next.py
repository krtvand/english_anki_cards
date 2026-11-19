from conftest import run

HEADER = ["english", "russian", "comment", "anki"]


def test_next_prints_the_topmost_pending_row(make_sheet, anki):
    sheet = make_sheet(
        HEADER,
        ["I have an older daughter", "У меня есть *старшая* дочь", "eldest?", ""],
        ["See you tomorrow", "Увидимся завтра", "", ""],
    )

    code, out = run(["next"], sheet, anki)

    assert code == 0
    assert out == {
        "row": 2,
        "english": "I have an older daughter",
        "russian": "У меня есть *старшая* дочь",
        "comment": "eldest?",
    }


def test_blank_added_and_discarded_rows_are_skipped(make_sheet, anki):
    sheet = make_sheet(
        HEADER,
        ["", "", "", ""],
        [],
        ["Thank you", "Спасибо", "", "1"],
        ["old junk", "старьё", "", "-"],
        ["", "", "a stray comment", ""],
        ["Take care", "Береги себя", "", ""],
    )

    code, out = run(["next"], sheet, anki)

    assert code == 0
    assert out["row"] == 7
    assert out["english"] == "Take care"


def test_english_only_row_is_offered(make_sheet, anki):
    sheet = make_sheet(HEADER, ["It's on me", "", "", ""])

    _, out = run(["next"], sheet, anki)

    assert out == {"row": 2, "english": "It's on me", "russian": "", "comment": ""}


def test_russian_only_row_is_offered(make_sheet, anki):
    sheet = make_sheet(HEADER, ["", "Я *угощаю*"])

    _, out = run(["next"], sheet, anki)

    assert out == {"row": 2, "english": "", "russian": "Я *угощаю*", "comment": ""}


def test_columns_are_found_by_header_name_and_unnamed_columns_ignored(make_sheet, anki):
    sheet = make_sheet(
        ["anki", "", "comment", "russian", "date", "english"],
        ["1", "old!старое", "", "Старое", "", "Old"],
        ["", "english!russian", "my note", "Новое", "2026-11-19", "New"],
    )

    _, out = run(["next"], sheet, anki)

    assert out == {"row": 3, "english": "New", "russian": "Новое", "comment": "my note"}


def test_nothing_left_when_no_pending_rows_remain(make_sheet, anki):
    sheet = make_sheet(HEADER, ["Thank you", "Спасибо", "", "1"], ["", "", "", ""])

    code, out = run(["next"], sheet, anki)

    assert code == 0
    assert out == {"nothing_left": True}


def test_exclude_steps_past_skipped_rows(make_sheet, anki):
    sheet = make_sheet(
        HEADER,
        ["I have an older daughter", "У меня *старшая* дочь", "", ""],
        ["See you tomorrow", "Увидимся завтра", "", ""],
        ["Take care", "Береги себя", "", ""],
    )

    _, out = run(["next", "--exclude", "2,3"], sheet, anki)

    assert out["row"] == 4
    assert out["english"] == "Take care"


def test_nothing_left_when_every_pending_row_is_skipped(make_sheet, anki):
    sheet = make_sheet(HEADER, ["See you tomorrow", "Увидимся завтра", "", ""])

    _, out = run(["next", "--exclude", "2"], sheet, anki)

    assert out == {"nothing_left": True}
