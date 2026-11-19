"""Pure helpers of the real adapters. The adapters themselves talk to live services and
are verified by hand (spec: Testing Decisions)."""

from pathlib import Path

import pytest

from anki_notes.adapters import (
    AnkiConnectError,
    credentials_path,
    find_repo_root,
    note_from_info,
    notes_from_infos,
    unwrap,
)


def test_notes_info_entry_is_flattened_to_id_and_the_three_fields():
    info = {
        "noteId": 1700000000001,
        "modelName": "Sentences",
        "tags": [],
        "fields": {
            "english": {"value": "My older daughter", "order": 0},
            "russian": {"value": "Моя *старшая* дочь", "order": 1},
            "comment": {"value": "eldest<br>is formal", "order": 2},
        },
    }
    assert note_from_info(info) == {
        "id": 1700000000001,
        "english": "My older daughter",
        "russian": "Моя *старшая* дочь",
        "comment": "eldest<br>is formal",
    }


def test_notes_info_entry_missing_a_field_reads_it_as_empty():
    info = {"noteId": 5, "fields": {"english": {"value": "Hi", "order": 0}}}
    assert note_from_info(info) == {"id": 5, "english": "Hi", "russian": "", "comment": ""}


def test_notes_info_leaves_out_unknown_ids_which_ankiconnect_answers_with_empty_entries():
    infos = [{}, {"noteId": 5, "fields": {"english": {"value": "Hi", "order": 0}}}]
    assert notes_from_infos(infos) == [{"id": 5, "english": "Hi", "russian": "", "comment": ""}]


def test_ankiconnect_reply_yields_its_result():
    assert unwrap("findNotes", {"result": [1, 2], "error": None}) == [1, 2]


def test_ankiconnect_error_is_raised_with_the_action_named():
    with pytest.raises(AnkiConnectError, match="addNote.*model was not found"):
        unwrap("addNote", {"result": None, "error": "model was not found: Sentences"})


def test_repo_root_is_the_nearest_folder_above_with_a_pyproject(tmp_path):
    (tmp_path / "pyproject.toml").write_text("")
    module_file = tmp_path / "src" / "anki_notes" / "adapters.py"
    module_file.parent.mkdir(parents=True)
    module_file.write_text("")
    assert find_repo_root(module_file) == tmp_path


def test_google_key_defaults_to_key_json_at_the_repo_root(tmp_path):
    assert credentials_path({}, tmp_path) == tmp_path / "key.json"


def test_google_key_comes_from_the_environment_when_set(tmp_path):
    env = {"GOOGLE_APPLICATION_CREDENTIALS": "/secrets/sa.json"}
    assert credentials_path(env, tmp_path) == Path("/secrets/sa.json")
