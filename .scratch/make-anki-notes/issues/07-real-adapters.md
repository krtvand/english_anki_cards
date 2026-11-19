# 07 — Real adapters: gspread Sheet + AnkiConnect, wiring

Status: done
Blocked by: 01

Spec: `../spec.md` ("Sheet adapter", "Anki adapter", "Configuration"); ADRs `docs/adr/0001-*`, `docs/adr/0002-*`.

## What to build

- Sheet adapter over gspread (service account), tab `phrases`, implementing the Sheet port (read all, update cells, insert row).
- Anki adapter over AnkiConnect HTTP at `http://127.0.0.1:8765` (version 6), implementing the Anki port (findNotes/notesInfo, addNote, updateNoteFields, sync).
- Google key from `GOOGLE_APPLICATION_CREDENTIALS`, default `key.json` at the repo root (already gitignored).
- Wire real adapters into the console script entry point.

## Acceptance criteria

- [x] Adapters are thin; not tested against the real services (spec says verified by hand). A unit test may cover pure helpers only.
- [x] `uv run anki-notes --help` works; dependencies added via `uv add`.
- [x] README section on one-time setup (AnkiConnect, share Sheet with service account, key.json).
