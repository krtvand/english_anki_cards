"""`anki-notes` console script: parse arguments, run a command, print its JSON."""

import argparse
import json
import sys
from typing import TextIO

from anki_notes import commands
from anki_notes.ports import AnkiPort, SheetPort


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
    update.add_argument("--new-comment", default="", help="new comment for the Note (plain text/Markdown)")
    return parser


def _add_row_reference(parser: argparse.ArgumentParser) -> None:
    """The Row reference every write command takes: Row number plus english/russian as `next` printed them."""
    parser.add_argument("--row", type=int, required=True, help="Row number as printed by next")
    parser.add_argument("--english", default="", help="the Row's english as printed by next")
    parser.add_argument("--russian", default="", help="the Row's russian as printed by next")


def _row_numbers(text: str) -> frozenset[int]:
    return frozenset(int(part) for part in text.split(",") if part.strip())


def run_command(argv: list[str], *, sheet: SheetPort, anki: AnkiPort, out: TextIO) -> int:
    """Run one command against the given ports, write its JSON to `out`, return the exit code."""
    args = _parser().parse_args(argv)
    try:
        if args.command == "next":
            result = commands.next_row(sheet, anki, exclude=args.exclude)
        elif args.command == "discard":
            result = commands.discard(sheet, anki, args.row, args.english, args.russian)
        elif args.command == "find":
            result = commands.find(anki, target=args.target, english=args.english)
        elif args.command == "update":
            result = commands.update(
                sheet, anki, args.row, args.english, args.russian,
                note_id=args.note_id, new_english=args.new_english, new_comment=args.new_comment,
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
