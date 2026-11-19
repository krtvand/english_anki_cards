"""`anki-notes` console script: parse arguments, run a command, print its JSON."""

import argparse
import json
import os
import sys
import traceback
from pathlib import Path
from typing import Callable, NoReturn, TextIO

from anki_notes import adapters, commands
from anki_notes import constants as c
from anki_notes.errors import CommandError
from anki_notes.ports import AnkiPort, Note, SheetPort
from anki_notes.reachability import Clock, ReachableAnki, SystemClock, launch_anki_app


class _Parser(argparse.ArgumentParser):
    """An argument parser whose usage errors become a CommandError (so: JSON, exit 1)."""

    def error(self, message: str) -> NoReturn:
        raise CommandError(f"{self.prog}: {message}")


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(prog="anki-notes")
    sub = parser.add_subparsers(dest="command", required=True)
    next_ = sub.add_parser("next", help="print the topmost Pending row")
    next_.add_argument(
        "--exclude",
        type=_row_numbers,
        default=frozenset(),
        help="comma-separated Row numbers to step past (Skipped Rows), e.g. 9,23",
    )
    discard = sub.add_parser("discard", help="mark a Row Discarded (-)")
    _add_row_reference(discard)
    add = sub.add_parser("add", help="add approved Note(s) to Anki, then update the Row and mark it 1")
    _add_row_reference(add)
    add.add_argument(
        "--notes-json",
        required=True,
        help='JSON list of Notes, e.g. \'[{"english": "...", "russian": "...", "comment": "..."}]\'; '
        "pass - to read it from stdin",
    )
    find = sub.add_parser("find", help="search the deck for Notes like this Row")
    find.add_argument("--target", default="", help="Target phrase; matches Notes whose russian contains it")
    find.add_argument(
        "--english",
        default="",
        help="english sentence; matches Notes whose english contains most of its significant "
        "words (3+ letters, not a stop word): all of them when there are one or two, "
        "otherwise at least two thirds",
    )
    update = sub.add_parser("update", help="Merge the Row into an existing Note and mark the Row 1")
    _add_row_reference(update)
    update.add_argument("--note-id", type=int, required=True, help="id of the Note to update, as find printed it")
    update.add_argument("--new-english", default="", help="new english for the Note")
    update.add_argument(
        "--new-comment", default="", help="replaces the Note's whole comment (plain text/Markdown)"
    )
    update.add_argument(
        "--append-comment",
        default="",
        help="added after the Note's existing comment, which is kept as it is (plain text/Markdown)",
    )
    update.add_argument(
        "--fields-json",
        default=None,
        help='instead of the --new-*/--append-* flags: a JSON object with any of "english", '
        '"comment", "append_comment"; pass - to read it from stdin',
    )
    sub.add_parser("sync", help="ask Anki to sync")
    return parser


def _load_json(text: str, flag: str):
    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        raise CommandError(f"{flag} is not valid JSON: {error}") from error


def _parse_notes(text: str) -> list[Note]:
    """The approved Notes from `--notes-json`: a list of {english, russian, comment} objects."""
    items = _load_json(text, "--notes-json")
    if not isinstance(items, list) or not items:
        raise CommandError("--notes-json must be a non-empty JSON list of Notes")
    notes = []
    for item in items:
        if not isinstance(item, dict) or not all(
            isinstance(item.get(k, ""), str) for k in (c.ENGLISH, c.RUSSIAN, c.COMMENT)
        ):
            raise CommandError("each Note in --notes-json must be an object with string english/russian/comment")
        notes.append(Note(item.get(c.ENGLISH, ""), item.get(c.RUSSIAN, ""), item.get(c.COMMENT, "")))
    return notes


_MERGE_KEYS = {c.ENGLISH: "new_english", c.COMMENT: "new_comment", "append_comment": "append_comment"}


def _parse_merge_fields(text: str) -> dict[str, str]:
    """The `update` keyword arguments from `--fields-json`: an object with english/comment/append_comment."""
    fields = _load_json(text, "--fields-json")
    if not isinstance(fields, dict) or not fields:
        raise CommandError('--fields-json must be a JSON object with any of "english", "comment", "append_comment"')
    unknown = set(fields) - set(_MERGE_KEYS)
    if unknown:
        raise CommandError(f"--fields-json has unknown key(s): {', '.join(sorted(unknown))}")
    if not all(isinstance(v, str) for v in fields.values()):
        raise CommandError("--fields-json values must be strings")
    return {_MERGE_KEYS[k]: v for k, v in fields.items()}


def _add_row_reference(parser: argparse.ArgumentParser) -> None:
    """The Row reference every write command takes: Row number plus english/russian as `next` printed them."""
    parser.add_argument("--row", type=int, required=True, help="Row number as printed by next")
    parser.add_argument("--english", default="", help="the Row's english as printed by next")
    parser.add_argument("--russian", default="", help="the Row's russian as printed by next")


def _row_numbers(text: str) -> frozenset[int]:
    return frozenset(int(part) for part in text.split(",") if part.strip())


def _dispatch(args: argparse.Namespace, sheet: SheetPort, anki: AnkiPort, stdin: TextIO) -> dict:
    def read(value: str) -> str:
        return stdin.read() if value == "-" else value

    if args.command == "next":
        return commands.next_row(sheet, exclude=args.exclude)
    if args.command == "discard":
        return commands.discard(sheet, args.row, args.english, args.russian)
    if args.command == "add":
        notes = _parse_notes(read(args.notes_json))
        return commands.add(sheet, anki, args.row, args.english, args.russian, notes)
    if args.command == "find":
        return commands.find(anki, target=args.target, english=args.english)
    if args.command == "update":
        flags = {"new_english": args.new_english, "new_comment": args.new_comment, "append_comment": args.append_comment}
        if args.fields_json is not None:
            if any(flags.values()):
                raise CommandError("give --fields-json or the --new-*/--append-* flags, not both")
            flags = _parse_merge_fields(read(args.fields_json))
        return commands.update(sheet, anki, args.row, args.english, args.russian, note_id=args.note_id, **flags)
    return commands.sync(anki)


def run_command(
    argv: list[str],
    *,
    sheet: SheetPort,
    anki: AnkiPort,
    out: TextIO,
    launch_anki: Callable[[], None] = launch_anki_app,
    clock: Clock | None = None,
    stdin: TextIO | None = None,
    err: TextIO | None = None,
) -> int:
    """Run one command against the given ports, write its JSON to `out`, return the exit code.

    The Anki port is wrapped so the first Anki call launches Anki (via `launch_anki`) and
    waits for it if it isn't answering. Every failure prints {"error": ...} and exits 1:
    a `CommandError` with its message as is; anything else as "<type>: <message>", with its
    traceback written to `err` (default: sys.stderr). `stdin` is where `-` reads from
    (default: sys.stdin)."""
    try:
        args = _parser().parse_args(argv)
        reachable = ReachableAnki(anki, launch=launch_anki, clock=clock or SystemClock())
        result, code = _dispatch(args, sheet, reachable, stdin or sys.stdin), 0
    except CommandError as error:
        result, code = {"error": str(error)}, 1
    except Exception as error:  # noqa: BLE001 - the boundary: every failure becomes JSON
        traceback.print_exc(file=err or sys.stderr)
        result, code = {"error": f"{type(error).__name__}: {error}"}, 1
    json.dump(result, out, ensure_ascii=False)
    out.write("\n")
    return code


def main() -> int:
    """Console script entry point: the real Sheet and Anki adapters, output to stdout."""
    repo_root = adapters.find_repo_root(Path(__file__).resolve())
    key_file = adapters.credentials_path(os.environ, repo_root)
    return run_command(
        sys.argv[1:],
        sheet=adapters.GSpreadSheet(key_file),
        anki=adapters.AnkiConnect(),
        out=sys.stdout,
    )


if __name__ == "__main__":
    sys.exit(main())
