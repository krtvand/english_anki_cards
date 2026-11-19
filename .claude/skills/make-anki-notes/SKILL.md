---
name: make-anki-notes
description: Turn Pending rows of the Sheet into Anki Notes, one Proposal at a time, then sync.
disable-model-invocation: true
---

# make-anki-notes

You run one session: take the topmost Pending row, write a Proposal, get the user's answer, write it through the `anki-notes` CLI, repeat, and sync at the end. You do all the language work; the CLI does all reading and writing. Vocabulary (Row, Pending row, Note, Target phrase, Alternative, Merge, Proposal, Skipped, Discarded) is defined in `GLOSSARY.md`.

## The CLI

Run every command from the repo root as `uv run anki-notes <command> ...`. Each prints one line of JSON. Any failure (bad arguments, Sheet or Anki trouble, a bug) prints `{"error": "..."}` and exits 1: show the user the message, and nothing else in that step counts as done. `add` and `update` are safe to re-run after a failure. The first command that touches Anki starts Anki itself if it is closed.

| Command | Prints |
|---|---|
| `next [--exclude 9,23]` | `{"row", "english", "russian", "comment"}` or `{"nothing_left": true}` |
| `find --target T --english E` | `{"notes": [{"id", "english", "russian", "comment"}, ...]}` |
| `add --row N --english E --russian R --notes-json -` | `{"row", "anki": "1", "notes": [{"id", "added"}, ...]}` |
| `update --row N --english E --russian R --note-id ID --fields-json -` | `{"row", "anki": "1", "note_id"}` |
| `discard --row N --english E --russian R` | `{"row", "anki": "-"}` |
| `sync` | `{"synced": true}` |

**Row reference.** `add`, `update` and `discard` take `--row`, `--english`, `--russian`: always the Row number and the *original* english and russian exactly as `next` printed them, never your Proposal's text. Pass an empty field as `--english ""`. The CLI uses them to find the Row again if the user added Rows on the phone mid-session, and refuses (changing nothing in the Sheet) when it can't find exactly one Row with that text; then tell the user and treat the Row as Skipped.

**`add` Notes.** Send the approved Notes as a JSON list on stdin, so quotes and line breaks survive the shell:

```sh
uv run anki-notes add --row 12 --english "My older daughter is ten." --russian "Моей *старшей* дочке десять." --notes-json - <<'EOF'
[{"english": "My oldest daughter is ten.", "russian": "Моей *старшей* дочке десять.", "comment": "..."}]
EOF
```

The first Note is written back to the source Row and marks it `1`; each further Note is added to Anki and inserted as a new Row directly below the source Row, marked `1`. `"added": false` means a Note with exactly that russian (or, for a Note with empty russian, exactly that english) was already in the deck and was reused, not duplicated. That makes `add` safe to re-run after any failure: run the same command again. It also means "add anyway" can't create a second Note with *identical* russian; vary the russian if the user wants one.

**`update` (Merge).** Send the changes as a JSON object on stdin, with any of these keys (leave out what stays as it is):

- `"append_comment"`: the Row's insight, added after the Note's existing comment, which is kept exactly as stored. **Prefer this for a Merge**: it loses nothing.
- `"english"`: replaces the Note's english.
- `"comment"`: replaces the Note's whole comment. Only when the user wants the comment rewritten; `find` prints it as Anki HTML, so the new one must restate everything worth keeping, in plain text/Markdown. Not together with `"append_comment"`.

```sh
uv run anki-notes update --row 14 --english "My eldest daughter" --russian "Моя *старшая* дочь" --note-id 1700000000001 --fields-json - <<'EOF'
{"append_comment": "**eldest** — старшая из трёх и более; *older* — из двух."}
EOF
```

The same is available as flags (`--new-english`, `--new-comment`, `--append-comment`), but stdin keeps quotes and line breaks intact. `update` marks the Row `1` and leaves its text unchanged.

Write comments in plain text or light Markdown (line breaks, `**bold**`, `-` lists); the CLI converts them to HTML for Anki and keeps them as typed in the Sheet.

## Session

Keep a session list of Skipped Row numbers, starting empty.

1. **Next Row.** `next --exclude <Skipped, comma-separated>` (omit `--exclude` while the list is empty). On `nothing_left`, tell the user the inbox is empty and go to step 6.
2. **Search.** `find --target <Target phrase> --english <english>`. The Target phrase is the text inside the `*asterisks*`, without them; with no marks, pass the whole russian. Use the Row's english, or your drafted english when the Row has none. Read every returned Note and judge whether it already teaches what this Row teaches.
3. **Proposal.** Write it by the rules in "Writing a Proposal" and show:
   - the Row as it is (row number, english, russian, comment);
   - each proposed Note, english / russian / comment, with **(changed)** beside exactly the fields that differ from the Row;
   - if a found Note is a likely duplicate: that Note, and the choices discard / add anyway / Merge (with the Merge you would make: which Note, the comment text to append, and a new english if any).

   Then ask: approve, edit, skip, or discard.
4. **Act.**
   - approve → `add` with the Notes (or `update` for an approved Merge).
   - edit → apply the user's changes, show the revised Proposal, ask again.
   - skip → add the Row number to the Skipped list; write nothing.
   - discard → `discard`.

   The step is done when the command printed its JSON without `error` (or, for skip, the list was updated). Report the result in one line.
5. **Offer the next Row** and loop to step 1 when the user agrees.
6. **Sync.** When the user stops or nothing is left, run `sync` once, so the Notes reach the phone. Report how many Rows were added, merged, discarded and skipped.

## Writing a Proposal

**english**
- The most common, everyday way a native speaker says it, American-leaning.
- If the Row's english is already that, keep it and say so explicitly: "your english is already right".
- If it is unnatural or wrong, replace it. Write it when the Row has none.
- One sentence, no inline `[a | b]` Alternatives: TTS reads this field.

**russian**
- Fix typos ("аллергеии" → "аллергии", "пол года" → "полгода"). Write it when the Row has none.
- When the russian is a question or explanation ("Как ответить, если тебя поблагодарили…"), turn it into a plain sentence to translate, and move the context into the comment.
- Keep the user's `*asterisks*` exactly as typed. Add marks only where the user typed them: a Row without marks teaches the whole sentence.

**comment** (in Russian, with English examples)
- Alternatives: other natural ways to say the Target phrase.
- British differences, when British English says it differently.
- Why your english beats the Row's, when you replaced it.
- Every fact about the language from the Row's comment, reworded and reorganised as needed. Drop chatbot filler ("Хочешь, я помогу…", "If you want, tell me…").
- Empty when there is nothing worth saying.

**Several Notes.** When one Row holds several things worth drilling (e.g. a pasted list of leaving-the-office phrases), propose one Note per phrase; the first replaces the Row, the rest become new Rows below it.

**Duplicates.** A found Note is a duplicate when it drills the same Target phrase in the same sense. Recommend Merge when the Row adds an insight to that Note (e.g. "eldest" vs "older"), discard when it adds nothing, add anyway when the sentence teaches the phrase in a usefully different context.
