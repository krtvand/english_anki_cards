"""`anki-notes` console script: parse arguments, run a command, print its JSON."""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Callable, TextIO

from anki_notes import adapters, commands
from anki_notes.ports import AnkiPort, SheetPort
from anki_notes.reachability import Clock, ReachableAnki, SystemClock, launch_anki_app


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
    sub.add_parser("sync", help="ask Anki to sync")
    return parser


def _add_row_reference(parser: argparse.ArgumentParser) -> None:
    """The Row reference every write command takes: Row number plus english/russian as `next` printed them."""
    parser.add_argument("--row", type=int, required=True, help="Row number as printed by next")
    parser.add_argument("--english", default="", help="the Row's english as printed by next")
    parser.add_argument("--russian", default="", help="the Row's russian as printed by next")


def _row_numbers(text: str) -> frozenset[int]:
    return frozenset(int(part) for part in text.split(",") if part.strip())


def run_command(
    argv: list[str],
    *,
    sheet: SheetPort,
    anki: AnkiPort,
    out: TextIO,
    launch_anki: Callable[[], None] = launch_anki_app,
    clock: Clock | None = None,
) -> int:
    """Run one command against the given ports, write its JSON to `out`, return the exit code.

    The Anki port is wrapped so the first Anki call launches Anki (via `launch_anki`) and
    waits for it if it isn't answering. A `CommandError` prints {"error": ...} and exits 1."""
    args = _parser().parse_args(argv)
    anki = ReachableAnki(anki, launch=launch_anki, clock=clock or SystemClock())
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
        elif args.command == "sync":
            result = commands.sync(anki)
        code = 0
    except commands.CommandError as error:
        result = {"error": str(error)}
        code = 1
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
