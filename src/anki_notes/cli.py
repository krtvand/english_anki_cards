"""`anki-notes` console script: parse arguments, run a command, print its JSON."""

import argparse
import json
import sys
from typing import TextIO

from anki_notes import commands
from anki_notes.ports import AnkiPort, Note, SheetPort


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="anki-notes")
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
    return parser


def _parse_notes(text: str) -> list[Note]:
    """The approved Notes from `--notes-json`: a list of {english, russian, comment} objects."""
    try:
        items = json.loads(text)
    except json.JSONDecodeError as error:
        raise commands.CommandError(f"--notes-json is not valid JSON: {error}") from error
    if not isinstance(items, list) or not items:
        raise commands.CommandError("--notes-json must be a non-empty JSON list of Notes")
    notes = []
    for item in items:
        if not isinstance(item, dict) or not all(
            isinstance(item.get(k, ""), str) for k in ("english", "russian", "comment")
        ):
            raise commands.CommandError(
                "each Note in --notes-json must be an object with string english/russian/comment"
            )
        notes.append(Note(item.get("english", ""), item.get("russian", ""), item.get("comment", "")))
    return notes


def _add_row_reference(parser: argparse.ArgumentParser) -> None:
    """The Row reference every write command takes: Row number plus english/russian as `next` printed them."""
    parser.add_argument("--row", type=int, required=True, help="Row number as printed by next")
    parser.add_argument("--english", default="", help="the Row's english as printed by next")
    parser.add_argument("--russian", default="", help="the Row's russian as printed by next")


def _row_numbers(text: str) -> frozenset[int]:
    return frozenset(int(part) for part in text.split(",") if part.strip())


def run_command(
    argv: list[str], *, sheet: SheetPort, anki: AnkiPort, out: TextIO, stdin: TextIO | None = None
) -> int:
    """Run one command against the given ports, write its JSON to `out`, return the exit code."""
    args = _parser().parse_args(argv)
    try:
        if args.command == "next":
            result = commands.next_row(sheet, anki, exclude=args.exclude)
        elif args.command == "discard":
            result = commands.discard(sheet, anki, args.row, args.english, args.russian)
        elif args.command == "add":
            notes_json = (stdin or sys.stdin).read() if args.notes_json == "-" else args.notes_json
            result = commands.add(
                sheet, anki, args.row, args.english, args.russian, _parse_notes(notes_json)
            )
        code = 0
    except commands.CommandError as error:
        result = {"error": str(error)}
        code = 1
    json.dump(result, out, ensure_ascii=False)
    out.write("\n")
    return code


def main() -> int:
    raise NotImplementedError("real Sheet and Anki adapters arrive in ticket 07")


if __name__ == "__main__":
    sys.exit(main())
