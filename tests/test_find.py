from fakes import FakeAnki

from anki_notes.ports import Note
from conftest import run


def deck():
    return FakeAnki(
        {
            11: Note("I have an older daughter", "У меня есть старшая дочь", "eldest?"),
            12: Note("She is my older sister", "Она моя старшая сестра", ""),
            13: Note("See you tomorrow", "Увидимся завтра", ""),
        }
    )


def test_find_by_target_phrase_matches_russian(make_sheet):
    code, out = run(["find", "--target", "старшая дочь"], make_sheet(["english"]), deck())

    assert code == 0
    assert out == {
        "notes": [
            {
                "id": 11,
                "english": "I have an older daughter",
                "russian": "У меня есть старшая дочь",
                "comment": "eldest?",
            }
        ]
    }


def test_find_by_english_matches_notes_sharing_most_significant_words(make_sheet):
    # "older", "daughter" and "have" all occur in note 11; note 12 shares only "older".
    code, out = run(
        ["find", "--english", "I have an older daughter."], make_sheet(["english"]), deck()
    )

    assert code == 0
    assert [n["id"] for n in out["notes"]] == [11]


def test_find_by_english_tolerates_one_differing_word(make_sheet):
    code, out = run(
        ["find", "--english", "I have an elder daughter"], make_sheet(["english"]), deck()
    )

    assert [n["id"] for n in out["notes"]] == [11]


def test_find_with_target_and_english_lists_each_note_once(make_sheet):
    code, out = run(
        ["find", "--target", "старшая", "--english", "I have an older daughter"],
        make_sheet(["english"]),
        deck(),
    )

    assert [n["id"] for n in out["notes"]] == [11, 12]


def test_find_returns_empty_list_when_nothing_matches(make_sheet):
    code, out = run(
        ["find", "--target", "угощаю", "--english", "It's on me"], make_sheet(["english"]), deck()
    )

    assert code == 0
    assert out == {"notes": []}


def test_find_by_target_matches_html_special_characters_as_anki_stores_them(make_sheet):
    anki = FakeAnki({31: Note("Tom and Jerry", "Том &amp; Джерри &lt;кот&gt;", "")})

    _, out = run(["find", "--target", "Том & Джерри <кот>"], make_sheet(["english"]), anki)

    assert [n["id"] for n in out["notes"]] == [31]


def test_find_escapes_anki_special_characters_in_user_text(make_sheet):
    anki = FakeAnki({21: Note("Ratio 1:2", "соотношение 1:2 *в* целом", "")})

    _, out = run(["find", "--target", "1:2 *в*"], make_sheet(["english"]), anki)

    assert [n["id"] for n in out["notes"]] == [21]
