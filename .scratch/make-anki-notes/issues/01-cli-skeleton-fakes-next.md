# 01 — CLI skeleton, in-memory fakes, `next`

Status: ready-for-agent
Blocked by: none

Spec: `../spec.md` (sections "CLI commands", "Sheet adapter", "Configuration", "Testing Decisions").

## What to build

The foundation every other ticket builds on:

- A `uv`-run console script (e.g. `anki-notes`) in a `src/` package, with pytest set up (`uv run pytest`).
- The command layer as the one test seam: commands take a Sheet port and an Anki port and return/print JSON.
- Sheet port + an in-memory fake (a grid of Rows with a header row). Anki port + an in-memory fake (a deck of Notes with ids). Keep the ports small; later tickets extend them.
- Constants module: spreadsheet id, tab `phrases`, deck `Sentenses`, note type `Sentences`, column headers, markers (`""` Pending, `1` Added, `-` Discarded).
- The `next` command.

## Acceptance criteria

- [ ] `next` prints the topmost Pending row: Row number (sheet row number, header = 1) plus english, russian, comment.
- [ ] Blank, Added (`1`) and Discarded (`-`) Rows are skipped.
- [ ] english-only and russian-only Rows are offered.
- [ ] Columns are found by header name, even when moved; unnamed columns are ignored.
- [ ] Prints a nothing-left result when no Pending rows remain.
- [ ] Supports a skip argument (e.g. `--exclude 9,23`) so the skill can step past Skipped Rows.
- [ ] Tests through the command layer against the fakes only.
