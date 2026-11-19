"""`anki-notes` console script: parse arguments, run a command, print its JSON."""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import TextIO

from anki_notes import adapters, commands
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
    return parser


def _row_numbers(text: str) -> frozenset[int]:
    return frozenset(int(part) for part in text.split(",") if part.strip())


def run_command(argv: list[str], *, sheet: SheetPort, anki: AnkiPort, out: TextIO) -> int:
    """Run one command against the given ports, write its JSON to `out`, return the exit code."""
    args = _parser().parse_args(argv)
    if args.command == "next":
        result = commands.next_row(sheet, anki, exclude=args.exclude)
    json.dump(result, out, ensure_ascii=False)
    out.write("\n")
    return 0


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
