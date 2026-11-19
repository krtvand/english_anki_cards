"""`anki-notes` console script: parse arguments, run a command, print its JSON."""

import argparse
import json
import sys
from typing import Callable, TextIO

from anki_notes import commands
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
    sub.add_parser("sync", help="ask Anki to sync")
    return parser


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
        elif args.command == "sync":
            result = commands.sync(anki)
    except commands.CommandError as e:
        _print(out, {"error": str(e)})
        return 1
    _print(out, result)
    return 0


def _print(out: TextIO, result: dict) -> None:
    json.dump(result, out, ensure_ascii=False)
    out.write("\n")


def main() -> int:
    raise NotImplementedError("real Sheet and Anki adapters arrive in ticket 07")


if __name__ == "__main__":
    sys.exit(main())
