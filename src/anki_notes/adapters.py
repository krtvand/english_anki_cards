"""Real adapters: the "phrases" tab through gspread, the deck through AnkiConnect (ADR 0001).
Thin by design and not tested against the live services (verified by hand); only the pure
helpers at the top are unit-tested. Both adapters connect lazily, so `--help` needs neither."""

import json
import urllib.request
from collections.abc import Iterable, Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from anki_notes import constants as c
from anki_notes.errors import CommandError

ANKICONNECT_URL = "http://127.0.0.1:8765"
ANKICONNECT_VERSION = 6


class AnkiConnectError(CommandError):
    """AnkiConnect answered with an error, or stopped answering mid-command."""


def unwrap(action: str, reply: dict) -> Any:
    """The `result` of an AnkiConnect reply; raises AnkiConnectError if it carries an `error`."""
    if reply.get("error") is not None:
        raise AnkiConnectError(f"AnkiConnect {action} failed: {reply['error']}")
    return reply.get("result")


def note_from_info(info: dict) -> dict:
    """One `notesInfo` entry flattened to its id and the `Sentences` fields."""
    fields = info.get("fields", {})

    def value(name: str) -> str:
        return fields.get(name, {}).get("value", "")

    return {
        "id": info["noteId"],
        "english": value(c.ENGLISH),
        "russian": value(c.RUSSIAN),
        "comment": value(c.COMMENT),
    }


def notes_from_infos(infos: list[dict]) -> list[dict]:
    """A `notesInfo` reply flattened; the empty entries AnkiConnect gives unknown ids are left out."""
    return [note_from_info(info) for info in infos if info.get("noteId") is not None]


def sheet_error(error: Exception, *, spreadsheet_id: str, tab: str) -> CommandError:
    """A gspread error as a CommandError that says what went wrong and what to do."""
    from gspread.exceptions import APIError, SpreadsheetNotFound, WorksheetNotFound

    if isinstance(error, SpreadsheetNotFound):
        return CommandError(
            f"spreadsheet {spreadsheet_id} not found or not shared with the service account "
            "(share it with the client_email in the key file)"
        )
    if isinstance(error, WorksheetNotFound):
        return CommandError(f'no tab "{tab}" in spreadsheet {spreadsheet_id}')
    if isinstance(error, APIError) and error.code == 403:
        return CommandError(
            f"Google Sheets permission denied for spreadsheet {spreadsheet_id}: share it with the "
            f"service account as an editor ({error.error.get('message', '')})"
        )
    return CommandError(f"Google Sheets error: {error}")


def find_repo_root(start: Path) -> Path:
    """The nearest folder at or above `start` holding `pyproject.toml`; the current folder if none."""
    for folder in [start, *start.parents]:
        if (folder / "pyproject.toml").is_file():
            return folder
    return Path.cwd()


def credentials_path(environ: Mapping[str, str], repo_root: Path) -> Path:
    """The Google service account key: `GOOGLE_APPLICATION_CREDENTIALS`, else `key.json` at the repo root."""
    explicit = environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    return Path(explicit) if explicit else repo_root / "key.json"


class GSpreadSheet:
    """The "phrases" tab of the spreadsheet, through a Google service account."""

    def __init__(self, key_file: Path, spreadsheet_id: str = c.SPREADSHEET_ID, tab: str = c.TAB):
        self._key_file = key_file
        self._spreadsheet_id = spreadsheet_id
        self._tab = tab
        self._worksheet = None

    def _ws(self):
        if self._worksheet is None:
            import gspread

            if not self._key_file.is_file():
                raise CommandError(
                    f"Google service account key not found at {self._key_file} "
                    "(set GOOGLE_APPLICATION_CREDENTIALS or put key.json at the repo root)"
                )
            with self._translated_errors():
                client = gspread.service_account(filename=self._key_file)
                self._worksheet = client.open_by_key(self._spreadsheet_id).worksheet(self._tab)
        return self._worksheet

    @contextmanager
    def _translated_errors(self) -> Iterator[None]:
        from gspread.exceptions import GSpreadException

        try:
            yield
        except GSpreadException as error:
            raise sheet_error(error, spreadsheet_id=self._spreadsheet_id, tab=self._tab) from error

    def read_all(self) -> list[list[str]]:
        """Every row, header first (index 0 = sheet row 1)."""
        ws = self._ws()
        with self._translated_errors():
            return [[str(cell) for cell in row] for row in ws.get_all_values()]

    def update_cells(self, row_number: int, values: dict[int, str]) -> None:
        """Write cells of one sheet row (1-based); keys are 0-based column indexes."""
        from gspread.cell import Cell

        cells = [Cell(row_number, col + 1, value) for col, value in values.items()]
        if cells:
            ws = self._ws()
            with self._translated_errors():
                ws.update_cells(cells, value_input_option="RAW")

    def insert_row(self, row_number: int, values: list[str]) -> None:
        """Insert a row so that it becomes sheet row `row_number`; rows below shift down."""
        ws = self._ws()
        with self._translated_errors():
            ws.insert_row(values, index=row_number, value_input_option="RAW", inherit_from_before=True)


class AnkiConnect:
    """The `Sentenses` deck in the running Anki, through the AnkiConnect add-on."""

    def __init__(self, url: str = ANKICONNECT_URL, deck: str = c.DECK, model: str = c.NOTE_TYPE):
        self._url = url
        self._deck = deck
        self._model = model

    def _invoke(self, action: str, **params: Any) -> Any:
        body = json.dumps(
            {"action": action, "version": ANKICONNECT_VERSION, "params": params}
        ).encode()
        request = urllib.request.Request(
            self._url, data=body, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                reply = json.load(response)
        except OSError as error:  # URLError, refused/reset connections and timeouts
            raise AnkiConnectError(f"couldn't talk to AnkiConnect ({action}): {error}") from error
        return unwrap(action, reply)

    def ping(self) -> bool:
        """True if AnkiConnect answers."""
        try:
            self._invoke("version")
        except AnkiConnectError:
            return False
        return True

    def find_notes(self, query: str) -> list[int]:
        """Note ids matching an Anki search query (not limited to the deck: add `deck:` yourself)."""
        return list(self._invoke("findNotes", query=query))

    def notes_info(self, ids: Iterable[int]) -> list[dict]:
        """Each note as {id, english, russian, comment}."""
        ids = list(ids)
        if not ids:
            return []
        return notes_from_infos(self._invoke("notesInfo", notes=ids))

    def add_note(self, english: str, russian: str, comment: str) -> int:
        """Add a `Sentences` note to the deck, no tags; returns its id."""
        note = {
            "deckName": self._deck,
            "modelName": self._model,
            "fields": {c.ENGLISH: english, c.RUSSIAN: russian, c.COMMENT: comment},
            "tags": [],
            "options": {"allowDuplicate": True},
        }
        return int(self._invoke("addNote", note=note))

    def update_note(self, note_id: int, fields: dict[str, str]) -> None:
        """Overwrite the given fields of an existing note."""
        self._invoke("updateNoteFields", note={"id": note_id, "fields": fields})

    def sync(self) -> None:
        """Run Anki's own sync with AnkiWeb."""
        self._invoke("sync")
