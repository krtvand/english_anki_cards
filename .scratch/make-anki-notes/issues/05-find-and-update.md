# 05 — `find` and `update` (Merge)

Status: done
Blocked by: 02

Spec: `../spec.md` ("CLI commands: find, update"; user stories 26–30).

## What to build

- `find`: search the deck by Target phrase and/or english words; print matching Notes with id and fields (english, russian, comment). Matching is plain text search (AnkiConnect `findNotes` query semantics: deck-scoped, field contains); the fake implements an equivalent substring/word match.
- `update`: Merge. Given a Row reference, an existing Note id and new english and/or comment, update that Note (comment converted to HTML as in 03 — reuse it), then mark the Row `1`. Adds no Note. Does not rewrite the Row's text.

## Acceptance criteria

- [x] `find` returns Notes matching by Target phrase in russian and by english words; returns empty list when none.
- [x] `update` changes the existing Note's fields, adds no Note, marks the Row `1`.
- [x] `update` on an unknown Note id fails clearly and leaves the Sheet unchanged.
