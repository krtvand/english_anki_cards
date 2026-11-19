# Spec: make-anki-notes — from Sheet Rows to Anki Notes

Status: ready-for-agent

Vocabulary: `GLOSSARY.md`. Decisions: `docs/adr/0001-ankiconnect-not-direct-collection.md`, `docs/adr/0002-sheet-is-an-inbox.md`. The design discussion that produced this spec is in `grill-me.md`.

## Problem Statement

I learn English with Anki flash cards in the `Sentenses` deck. During the day I jot sentences down from any device in the "phrases" tab of a Google spreadsheet (the Sheet): an english sentence, its russian, sometimes a comment, and in the russian I mark with `*asterisks*` the Target phrase whose translation I actually want to remember.

Turning those Rows into Notes is slow, manual work. For each Row I have to work out the most natural, everyday English for the sentence, check whether my own english is right, collect Alternatives for the Target phrase, merge that with whatever comment I already pasted (often a long chatbot answer), fix typos in the russian, copy all of it into Anki, and then go back to the Sheet and mark the Row `1`. Rows pile up: 59 Pending rows sit in the Sheet today. Some are messy: no english, no russian, a question instead of a sentence, a pasted phrasebook, or a near-duplicate of a Note I already have.

## Solution

In Claude Code I run the `make-anki-notes` skill. It takes the topmost Pending row, searches the deck for Notes I may already have, and shows me a Proposal:

- the most natural english, or an explicit "your english is already right"
- a cleaned-up russian with the Target phrase marks as I typed them
- a Russian-language comment that keeps everything I had and adds the Alternatives

Changed fields are marked. A Row may yield more than one Note. If the deck already has the Note, I can discard the Row, add it anyway, or Merge it into the existing Note.

I approve, edit then approve, skip, or discard. On approval, the Note goes into Anki and the Row is updated with the final text and marked `1`; a Discarded Row is marked `-`. Then the skill offers the next Row. When I stop, Anki syncs so the new Notes reach my phone.

Claude does all the language work. A small Python CLI does all the reading and writing, so it never has to guess or call a model.

## User Stories

1. As a learner, I want to start the whole flow by running one Claude Code skill, so that turning Rows into Notes needs no setup per session.
2. As a learner, I want the skill to pick the topmost Pending row, so that the Rows I added most recently (at the top) are handled first.
3. As a learner, I want blank Rows to be skipped, so that empty lines in the Sheet never become Proposals.
4. As a learner, I want a Row with an english but no russian to be offered, so that a phrase I only know in English still becomes a Note.
5. As a learner, I want a Row with a russian but no english to be offered, so that I can jot down only the Russian and get the English from Claude.
6. As a learner, I want the english in the Proposal to be the most common, everyday way to say the sentence, so that I learn what native speakers actually say.
7. As a learner, I want the Proposal to tell me explicitly when my own english is already the most natural choice, so that I know it was checked and not just kept.
8. As a learner, I want my english replaced when it is unnatural or wrong, so that I never drill a mistake.
9. As a learner, I want the target English to be American-leaning, with British differences mentioned in the comment, so that I learn one consistent variety and still recognise the other.
10. As a learner, I want other natural ways to say the Target phrase listed as Alternatives in the comment, so that I recognise them when I hear them.
11. As a learner, I want the comment written in Russian with English examples, so that it matches my existing Notes.
12. As a learner, I want every fact about the language in my existing comment kept, so that notes I wrote or pasted are never lost.
13. As a learner, I want chatbot filler ("Хочешь, я помогу…", "If you want, tell me…") dropped from pasted comments, so that the back of the card stays readable.
14. As a learner, I want Claude to fix typos in my russian ("аллергеии", "пол года"), so that the front of the card is clean.
15. As a learner, I want Claude to write the russian when a Row has none, so that every Note has a front.
16. As a learner, I want a Row whose russian is a question or explanation ("Как ответить, если тебя поблагодарили…") turned into a plain sentence, so that the front of the card is something to translate.
17. As a learner, I want Claude never to add Target phrase marks I didn't type, so that a Row without marks means I want to learn the whole sentence.
18. As a learner, I want my `*asterisks*` kept in the russian exactly as typed, so that new Notes look like my 651 existing ones.
19. As a learner, I want Claude to propose several Notes from one Row when that is useful (e.g. a list of leaving-the-office phrases), so that one jotted Row can teach several phrases.
20. As a learner, I want each extra Note logged as a new Row inserted directly below its source Row and marked `1`, so that the Sheet stays a complete log of what is in Anki.
21. As a learner, I want only the changed fields marked in the Proposal, so that I can see at a glance what Claude changed.
22. As a learner, I want to approve a Proposal as it is, so that a good Proposal costs me one word.
23. As a learner, I want to edit a Proposal before approving it, so that I can adjust the wording without starting over.
24. As a learner, I want to skip a Row for this session, leaving it Pending, so that I can come back to a hard Row later.
25. As a learner, I want to discard a Row, marking it `-` without adding a Note, so that junk Rows like old leftovers are never offered again and the history stays visible.
26. As a learner, I want the skill to search the deck for Notes with the same Target phrase or a similar english before proposing, so that I don't drill the same thing twice.
27. As a learner, I want to see the matching Notes when a duplicate is found, so that I can judge whether the new Row adds anything.
28. As a learner, I want to Merge a Row into an existing Note, updating that Note's english or comment and marking the Row `1`, so that a later insight (e.g. "eldest" vs "older") lands on the Note I already study.
29. As a learner, I want to add a Note anyway when a match is found, so that a different sentence teaching the same Target phrase is still possible.
30. As a learner, I want the duplicate check against Anki to also catch duplicates between Pending rows, so that I don't need a separate check inside the Sheet.
31. As a learner, I want approved Notes to go into the `Sentences` note type in the `Sentenses` deck, so that they look and behave like my existing cards (russian on the front, english, comment and TTS on the back).
32. As a learner, I want the comment converted from the Sheet's plain text or Markdown to HTML in Anki, so that line breaks, bold and lists show properly on the card.
33. As a learner, I want the Sheet to keep the comment as plain text or Markdown, so that it stays readable on my phone.
34. As a learner, I want the approved english, russian and comment written back to the Row, so that the Sheet reads as a log of what went into Anki.
35. As a learner, I want the Row marked `1` only after its Notes are in Anki, so that `1` always means "in Anki".
36. As a learner, I want the right Row updated even if I added Rows on my phone during the session (which shifts every Row down), so that the tool never marks or overwrites the wrong Row.
37. As a learner, I want the tool to refuse to write when it can't find exactly one Row with the original content, so that an ambiguous Sheet never gets a wrong write.
38. As a learner, I want to be able to re-run an approval after a failure (e.g. the Sheet write failed after the Anki write succeeded) without getting a duplicate Note, so that recovering is just "run it again".
39. As a learner, I want the tool to start Anki itself if it isn't running and wait for it, so that I never have to remember to open Anki first.
40. As a learner, I want a clear message if Anki still can't be reached, so that I know what to fix.
41. As a learner, I want Anki to sync once at the end of the session, so that the new Notes reach my phone without a sync after every Note.
42. As a learner, I want the skill to offer the next Pending row after each one, so that I can work through the backlog in one sitting.
43. As a learner, I want the session to end, with a sync, when no Pending rows are left, so that I know the inbox is empty.
44. As a learner, I want later edits in the Sheet or in Anki not to travel to the other side, so that Anki owns a Note once its Row is Added and nothing overwrites my study edits.
45. As a learner, I want the tool to need only a one-time setup (AnkiConnect, sharing the Sheet with the service account, the Google key), so that day-to-day use is just running the skill.
46. As a developer, I want the CLI to do only deterministic reading and writing and print JSON, so that it can be tested and the skill can read its output reliably.
47. As a developer, I want the Sheet columns found by header name, not position, so that adding a column to the Sheet doesn't break the tool.
48. As a developer, I want settings (spreadsheet id, tab, deck, note type) as constants in the code, so that there is no config file for a single-user tool.
49. As a developer, I want the Google key read from `GOOGLE_APPLICATION_CREDENTIALS` with a default of `key.json` at the repo root (gitignored), so that the key is never committed.
50. As a developer, I want the agreed behaviour covered by tests that use in-memory fakes of the Sheet and Anki, so that I can change the code without touching my real Sheet or collection.

## Implementation Decisions

**Split of responsibilities**
- The **skill** `make-anki-notes` (a Claude Code project skill) owns all language work: choosing the english, Alternatives, merging and cleaning comments, russian fixes, deciding whether a match is a duplicate, and splitting a Row into several Notes. It runs the approval loop and calls the CLI. The skill is named with hyphens because skill names allow no underscores.
- The **CLI** (a `uv`-run console script in this project) owns all I/O and never calls a model. Every command prints JSON for the skill to read.

**CLI commands**
- `next`: the topmost Pending row: its Row number and its english, russian and comment. A Pending row has an empty `anki` cell and at least one of english/russian filled. Prints nothing-left when there are none.
- `find`: searches the deck for Notes by Target phrase and/or english words, and prints the matching Notes with their id and fields.
- `add`: given the Row reference and one or more Notes, adds the Notes to Anki, then writes the first Note's english/russian/comment back to the Row and marks it `1`. Each extra Note becomes a new Row inserted directly below the source Row, filled in and marked `1`.
- `update`: Merge. Given the Row reference, an existing Note id and the new english and/or comment, updates that Note in Anki, then marks the Row `1`.
- `discard`: given the Row reference, marks the Row `-`.
- `sync`: asks Anki to run its own sync.

**Row reference and finding the Row again**
- Every write command receives the Row number *and* the original english and russian as `next` printed them.
- Before writing, the command re-reads that Row number. If its english/russian still match, it writes there. Otherwise it searches the tab for Rows with exactly that original english and russian. One match: it writes there. Zero or several: it refuses and changes nothing in the Sheet.

**Order of writes and safe re-runs**
- Anki is written first, the Sheet second.
- Before adding a Note, `add` looks for a Note in the deck whose russian is exactly the same. If one exists, that Note is not added again and the command goes on to the Sheet step. Re-running `add` after any failure therefore finishes the job without duplicating. The flip side: "add anyway" never creates a second Note with *identical* russian.

**Sheet adapter**
- Talks to the "phrases" tab of the spreadsheet through gspread with the existing Google service account. The spreadsheet is shared with the service account as Editor (one-time manual step).
- Reads and writes go through the API; the public CSV export is not used.
- Columns `english`, `russian`, `comment`, `anki` are located by header name.
- Markers in `anki`: empty = Pending, `1` = Added, `-` = Discarded.

**Anki adapter**
- Talks to the running Anki through the AnkiConnect add-on over localhost HTTP (ADR 0001). AnkiConnect is installed by hand once.
- If AnkiConnect doesn't answer, the adapter launches Anki (`open -a Anki`) and polls for up to about 20 seconds, then fails with a message saying Anki couldn't be reached.
- Notes use the existing note type `Sentences` (fields `english`, `russian`, `comment`) in the deck `Sentenses`. Nothing about the note type or template is changed. No tags are added.

**Comment conversion**
- The Sheet holds comments as plain text or light Markdown. On the way to Anki, the comment is converted to HTML: line breaks to `<br>`, `**bold**` to bold, `*italic*`/`_italic_` to italic, `-`/`*`/`•` bullet lines to a list, headings to a heading. The russian field is *not* converted: its `*asterisks*` stay literal.
- Text sent to Anki is HTML-escaped before conversion, so `<`, `>` and `&` in a sentence render as text.

**Sheet is an inbox (ADR 0002)**
- No id links a Row to a Note. Once a Row is Added, Anki owns its Notes. The tool never reads Added Rows back into Anki or Notes back into the Sheet. Duplicates are found by searching Anki's text.

**Configuration**
- Constants in code: spreadsheet id, tab name, deck name, note type name, column headers, markers.
- The Google key comes from `GOOGLE_APPLICATION_CREDENTIALS`, defaulting to `key.json` at the repo root; `key.json` is added to `.gitignore`.

**Skill flow (one session)**
1. `next`; stop if nothing is left.
2. `find` with the Row's Target phrase and english.
3. Show the Proposal: the Row as it is, then the proposed Note(s), marking only changed fields. If `find` returned a likely duplicate, show it and offer discard / add anyway / Merge.
4. Act on the answer: approve or edit → `add` (or `update` for a Merge); discard → `discard`; skip → remember the Row as Skipped for this session and fetch the next Pending row after it.
5. Offer the next Row. When the user stops, or none are left, `sync`.

`next` needs a way to start after Skipped Rows, e.g. an optional "after Row N" or "exclude these Rows" argument. The skill holds the Skipped list for the session only.

## Testing Decisions

- **One seam:** the CLI's command layer, with the Sheet and Anki adapters replaced by in-memory fakes (a grid of Rows with a header row; a deck of Notes with ids). Tests run a command against the fakes and assert on what ends up in them and on the JSON printed. They don't look at internal functions.
- A good test describes behaviour a user would recognise ("adding a Row while a session is running doesn't make `add` mark the wrong Row"), sets up the fake Sheet and deck, runs one or two commands, and checks the outcome. Tests should not break when internals are refactored.
- **What to cover:**
  - `next`: picks the topmost Pending row; skips blank, Added and Discarded Rows; handles english-only and russian-only Rows; finds columns by header even when they move; reports nothing-left; respects the skip argument.
  - **Shifted Row:** a Row inserted above between `next` and `add` → the correct Row is written. Two Rows with the same content after a shift → refused, Sheet unchanged.
  - **Re-run:** the Sheet write fails after the Anki write → a second `add` finishes the Sheet step, and the deck still has exactly one such Note.
  - **Several Notes:** `add` with two Notes → two Notes in the deck; the source Row updated and marked `1`; a new Row inserted directly below with the second Note, marked `1`.
  - **Merge:** `update` changes the existing Note's fields, adds no Note, and marks the Row `1`.
  - **Discard:** marks `-`, deck unchanged.
  - **Comment conversion:** checked through `add` by inspecting the comment the fake deck received: line breaks, bold, lists, HTML escaping, and the russian's asterisks left literal.
  - **Anki not reachable:** with a fake that never answers, the command fails with the "couldn't reach Anki" message. The fake launcher is told to start Anki once.
- **Not tested automatically:** the real gspread and AnkiConnect adapters (thin; verified by hand once against the real Sheet and collection), the skill's language work, and the real launch of the Anki app.
- **Tooling:** pytest, run with `uv run pytest`.
- **Prior art:** none in this repo. The Greek interview project (`/Users/krtvand/Greek/Greek/citizenship_interview`) tests its export and import against throwaway Anki collections. Here the fakes play that role, because writes go through AnkiConnect rather than the collection file.

## Out of Scope

- Syncing edits between the Sheet and Anki after a Row is Added, in either direction.
- Changing the `Sentences` note type, its card template or its styling (e.g. rendering the Target phrase in bold).
- Audio: the card's AwesomeTTS tag already speaks the english on the fly.
- Tags on new Notes.
- The other tabs of the spreadsheet ("English words", "russian", "Greek", …) and the other decks.
- Cleaning up or re-checking the 667 Rows already Added or the 651 existing Notes.
- Running without Anki on this Mac (e.g. writing straight to AnkiWeb).
- Any LLM calls from the CLI.

## Further Notes

- One-time setup, by hand: install the AnkiConnect add-on; share the spreadsheet with `andrey-kartaev@constant-wonder-383212.iam.gserviceaccount.com` as Editor; copy `key.json` from the Greek project to the repo root.
- Today's Sheet: 59 Pending rows (rows 9–67, plus old leftovers such as row 707), rows 2–8 blank. Rows 9 and 23 are a near-duplicate pair ("older daughter"), which is a good first manual test of Merge.
- A few old Rows have text in an unnamed column (`english!russian`), a leftover from an earlier import. The tool ignores columns it doesn't name.
- The `english` field in some existing Notes holds inline Alternatives like `[appearance | look]`. New Notes keep Alternatives in the comment instead, so the english is a single sentence that TTS reads cleanly.
