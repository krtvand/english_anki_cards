# Grill: English Anki cards — design questions

Source: `spec.md`. Answer under each question (`Answer:`); "yes" accepts the recommendation.

## Findings so far

- **Sheet:** the tab is **"phrases"** (gid `1182668649`), columns `english | russian | comment | anki`.
  New rows are added **at the top**: rows 9–67 have an empty `anki`, rows 2–8 are blank, and a few
  old rows (e.g. 707) also have an empty `anki`. The other 667 rows are marked `1`.
- **Anki:** deck `Sentenses`, note type `Sentences` with fields `english | russian | comment`, one card
  (front: russian; back: english + comment + AwesomeTTS). Asterisks are kept literally in `russian`,
  comments are HTML, and the existing notes have no tags. 651 notes.
- **Tools:** AnkiConnect is **not** installed (only AwesomeTTS). The sheet can be read publicly as CSV
  with no login, but writing needs auth. The Greek project's `key.json` is a service account
  (`andrey-kartaev@constant-wonder-383212.iam.gserviceaccount.com`).
- **Messy rows:** some have no English, some have no Russian (20, 33, 49), some have a question or a
  pasted chat answer in the Russian cell (15, 27, 43, 50), and some are near-duplicates (9 and 23,
  "older daughter").

## Round 1

### Q1 — Which tab
Is the tool's input the **"phrases"** tab only, with the column headers `english`, `russian`,
`comment`, `anki` used as names?

**Recommended:** Yes. Columns are found by header name, not position, so adding a column later
doesn't break anything.

Answer: ok

### Q2 — What "next row" means
New rows are added at the top. Should "next" mean the **topmost** row where `anki` is empty and at
least one of english/russian is filled? Blank rows (2–8) would be skipped.

**Recommended:** Yes, top-down, skipping blank rows. Old leftovers like row 707 come up eventually
and can be discarded then (see Q11).

Answer: ok

### Q3 — How to write to Anki
- **(a) AnkiConnect add-on.** Anki must be **running**. You install one add-on, and the CLI talks to
  it over HTTP on localhost. Anki's own sync takes notes to the phone.
- **(b) Open the collection directly, as in the Greek project.** Anki must be **quit**. Needs the
  `anki` Python library, a backup step and AnkiWeb sync code.
- **(c) Build a `.apkg` and import it by hand.**

**Recommended:** (a) AnkiConnect. We only ever *add* notes to an existing note type, so the Greek
project's protections (fixed note type id, mod timestamps, full-sync guard) don't apply. The cost is
that Anki must be open when you approve a note.

Answer: ok

### Q4 — How to write to the sheet
Should the CLI use **gspread with the existing service account**, with the sheet shared with
`andrey-kartaev@…iam.gserviceaccount.com` as Editor?

**Recommended:** Yes. It's already set up, needs no browser OAuth flow, and reads go through the same
API instead of the public CSV export. The alternative is OAuth as yourself, with token refreshes.

Answer: ok

### Q5 — Sheet is an inbox, not the source of truth
Once a row is marked `1`, does **Anki own the note**? Later edits to the row would *not* sync to
Anki, and edits in Anki would not flow back to the sheet.

**Recommended:** Yes. That's how the 667 existing rows already work: nothing links rows to notes,
and building that link is the most expensive part of the Greek project. When a note is approved, the
final english/comment are written back to the row so the sheet stays a readable log.

Answer: ok

### Q6 — Note type and asterisks
Should new notes go into the existing **`Sentences` note type in the `Sentenses` deck**, with the
Russian stored **with its `*asterisks*` literally**, as in the 651 existing notes?

**Recommended:** Yes, keep it consistent. Showing the marked part in bold on the card is a separate
change to the card template and can come later.

Answer: ok

### Q7 — One row → one note
Should every row always produce **exactly one note**? This includes "phrasebook" rows like 42 (a list
of leaving-the-office phrases) and rows where the Russian cell is a question, like 15 ("Как
ответить, если тебя поблагодарили…"). For those, Claude proposes one real sentence pair for the
front and back and puts the rest into the comment.

**Recommended:** Yes. Splitting one row into several notes means inventing new rows or losing the
row↔note mapping. If you want a second card from a list, add it as a new row.

Answer: there is not strict rule for one to one mapping. if you think two notes will be useful we can create them

### Q8 — Claude may change the Russian
Can Claude **propose** edits to the `russian` cell? That covers:
- fixing typos ("аллергеии", "пол года", "высмаркиватся")
- writing the Russian when it's missing (rows 20, 33, 49)
- turning a meta-question (15, 27) into a plain sentence

The edits are always shown in the proposal and written back to the sheet on approval.

**Recommended:** Yes. The Russian is the front of the card, so it has to be clean. Claude doesn't
*add* asterisks on its own. If a row has none, the whole sentence is what you're learning.

Answer: ok

### Q9 — Which English, and which language for comments
Is the target **natural, everyday American-leaning English**, with British alternatives mentioned in
the comment where they differ? And are the comments written **in Russian**, with English examples?

**Recommended:** Yes to both, matching most of the existing comments.

Answer: ok

### Q10 — Comment format
The sheet's comments are plain text, sometimes with Markdown pasted from chats (rows 42, 55). The
Anki field is HTML. Should the **sheet keep plain text/Markdown**, with the CLI **converting it to
HTML** for Anki (line breaks → `<br>`, `**bold**` → `<b>`, lists → `<ul>`)?

**Recommended:** Yes. The sheet stays readable on a phone, and the card renders properly.

Answer: ok

### Q11 — Skip and discard
In a session you can **approve**, **edit then approve**, **skip** (move on and leave the row empty,
so it comes back next time) or **discard**. Discard covers junk or duplicate rows like 707: should it
mark the row `-` in `anki` so the tool never offers it again, without adding a note?

**Recommended:** Yes: `1` means added, `-` means discarded on purpose. No deleting rows by hand,
and the history stays visible.

Answer: ok

### Q12 — Who does what
- **Skill** `make-anki-notes` in `.claude/skills/`: all the language work (translation,
  alternatives, merging comments, duplicate judgement) and the approval loop.
- **Python CLI** (`uv run anki-cards …`): deterministic I/O only, with three commands: `next`
  (print the next row as JSON), `find` (search Anki for similar notes), and `add` (add the note to
  Anki, write the row back, mark `1`).

**Recommended:** Yes. Same shape as the Greek project: the CLI is testable and never calls an LLM.

Answer: ok

## Round 2

Settled in round 1: everything as recommended, except Q7 — a Row may yield **several Notes** when
that is useful. Vocabulary is now in `GLOSSARY.md` (Sheet, Row, Pending row, Added, Discarded,
Skipped, Note, Target phrase, Alternative, Proposal).

New fact that matters here: because you add Rows **at the top**, every Row number shifts down by
one whenever you add a Row on your phone, including in the middle of a session.

### Q13 — How a Row with several Notes is logged in the Sheet
When one Row yields two Notes (e.g. row 42's list of phrases → "I'm heading out" and "I'm off for
the day"), how does the Sheet record the second one?
- **(a)** The first Note's text is written back to the source Row. Each extra Note becomes a **new
  Row inserted directly below it**, also marked `1`.
- **(b)** Only the source Row is updated. Extra Notes exist only in Anki.

**Recommended:** (a). It keeps "one Row = one Note" true *after* the fact, so the Sheet stays a
complete log, and the extra Rows are already marked `1`, so they are never offered again.

Answer: ok

### Q14 — What to do when the Note already exists in Anki
Before proposing, Claude searches Anki for Notes with the same Target phrase or similar english
(e.g. row 23 "my older daughter" will find row 9's Note once that is Added). If a match is found,
the choices are:
- **discard** the Row (`-`)
- **add anyway** (a different sentence teaching the same phrase is still useful)
- **merge into the existing Note**: update that Note's english/comment in Anki and mark the Row
  `1`, adding nothing new

Should all three be offered?

**Recommended:** Yes. Merge is the one that adds work (the CLI needs an `update` command), but it's
exactly what row 23 calls for: its comment about "eldest" belongs on row 9's Note.

Answer: ok

### Q15 — No separate duplicate check inside the Sheet
Rows are processed one at a time and each Added Row is in Anki right away, so the Anki check in Q14
also catches duplicates between Pending rows (9 then 23). Is it OK to have **no Sheet-to-Sheet
check**?

**Recommended:** Yes.

Answer: ok

### Q16 — Finding the Row again when it's time to write
Row numbers can shift during a session (see above). When writing back, the CLI is given the Row
number *and* the original english/russian it read. Should it:
- re-read that Row and check the content still matches
- if it doesn't, find the Row by its original content, and refuse if it is not exactly one Row

**Recommended:** Yes. Without this, adding a Row on your phone mid-session would make the tool mark
or overwrite the wrong Row.

Answer: ok

### Q17 — Anki written first, then the Sheet, and `add` is safe to re-run
If the Anki write succeeds and the Sheet write fails (network, quota), a re-run must not add the
Note twice. Should `add`:
- write to Anki first, then the Sheet
- before adding, look for a Note with exactly the same russian in the deck and, if found, skip the
  Anki step and only finish the Sheet step

**Recommended:** Yes. Re-running after any failure then just finishes the job.

Answer: ok

### Q18 — Cleaning existing comments
The spec says not to drop existing comment content and to combine it. Some comments are pasted chat
replies with filler: "Хочешь, я помогу подобрать…" (row 50), "If you want, tell me: spoken vs
chat…" (row 42). May Claude **drop chatbot filler and reword/reorganise** the comment, as long as
every *fact about the language* is kept?

**Recommended:** Yes. The rewritten comment is always in the Proposal, so you see what changed.

Answer: ok

### Q19 — Getting notes to the phone
AnkiConnect can trigger Anki's own sync. Should the skill **sync once at the end of a session**
(when you stop or there are no Pending rows), not after each Note?

**Recommended:** Yes. One sync per session; each sync takes a few seconds.

Answer: ok

### Q20 — When Anki isn't running
AnkiConnect only works with Anki open. Should the CLI **start Anki itself** (`open -a Anki`) and
wait up to ~20 seconds for AnkiConnect, failing with a clear message after that?

**Recommended:** Yes. You never have to remember to open Anki first.

Answer: ok

### Q21 — Tag new Notes
Your existing Notes have no tags. Should Notes created by the tool get a tag, e.g. `from-sheet`?

**Recommended:** Yes. It costs nothing on the card and lets you find everything the tool made
(`tag:from-sheet`) if something ever goes wrong.

Answer: i don't need tags at the moment

### Q22 — Where settings and the key live
- The sheet id, tab name, deck, note type and tag are **constants in the code**, with no config file.
- The Google key is read from `GOOGLE_APPLICATION_CREDENTIALS`, defaulting to `key.json` at the
  repo root (gitignored), which you copy from the Greek project.

Is that OK?

**Recommended:** Yes. There's one user and one sheet, so a config file would be ceremony.

Answer: ok

### Q23 — What a Proposal shows
For each Row the Proposal shows the Row as it is, then the proposed english / russian / comment,
with **only the changed fields marked**. If the existing english is already the most natural
choice, it says so explicitly rather than silently keeping it. Does that work?

**Recommended:** Yes.

Answer: ok

### Q24 — Tests
- **pytest**, with fake Sheet and fake Anki clients, covering: choosing the next Pending row,
  finding a shifted Row (Q16), re-running `add` after a failure (Q17), inserting extra Rows (Q13),
  and Markdown → HTML for comments.
- No automated tests against the real Sheet or your real Anki. That's checked by hand once.

Is that the right scope?

**Recommended:** Yes.

Answer: ok

### Q25 — Record two decisions as ADRs
Two decisions will surprise a future reader who knows the Greek project:
1. **AnkiConnect, not opening the collection directly**: the Greek project does the opposite.
2. **The Sheet is an inbox; Rows aren't linked to Notes**: the Greek project keeps a source of
   truth with ids.

Should I write these as `docs/adr/0001-…` and `0002-…`?

**Recommended:** Yes, a paragraph each.

Answer: ok

## Outcome

Round 2 settled as recommended, except Q21: **no tags**. No open questions remain.
Vocabulary: `GLOSSARY.md`. Decisions: `docs/adr/0001-ankiconnect-not-direct-collection.md`,
`docs/adr/0002-sheet-is-an-inbox.md`.

### The design in one page

**One-time setup (by hand):** install the AnkiConnect add-on; share the spreadsheet with the
service account as Editor; copy `key.json` from the Greek project to the repo root (gitignored).

**Skill `make-anki-notes`** (`.claude/skills/make-anki-notes/SKILL.md`), one loop per session:
1. `next` → the topmost Pending row of the "phrases" tab (blank Rows skipped).
2. `find` → Notes in `Sentenses` with the same Target phrase or similar english.
3. Claude writes a Proposal: the most natural, everyday (American-leaning) english; Alternatives
   for the Target phrase and British differences in a Russian-language comment; the existing
   comment kept and merged (chatbot filler may go, language facts may not); typo fixes or a
   missing russian, never new asterisks. Only changed fields are marked; an already-good english
   is said to be good. It may propose several Notes for one Row. If `find` hit a match, it offers
   discard / add anyway / Merge.
4. You approve, edit then approve, skip, or discard.
5. On approval, `add` (or `update` for a Merge); on discard, `discard`. Then offer the next Row.
6. When you stop, or no Pending rows are left, `sync` (Anki's own sync, to reach the phone).

**CLI** (`uv run anki-cards …`), deterministic I/O, no LLM:
- `next`: print the next Pending row as JSON (Row number + its english/russian/comment).
- `find`: search the deck, print matching Notes as JSON.
- `add`: add the Note(s) via AnkiConnect, then write the Row back and mark it `1`; extra Notes
  become new Rows inserted directly below, marked `1`. Anki first; a Note with exactly the same
  russian already in the deck is not added again, so a re-run after a failure just finishes.
- `update`: Merge into an existing Note, then mark the Row `1`.
- `discard`: mark the Row `-`.
- `sync`: trigger Anki's sync.
- Every Sheet write re-reads the Row by number and checks it still holds the original
  english/russian; otherwise it finds the Row by that content, and refuses unless exactly one
  Row matches.
- Starts Anki (`open -a Anki`) and waits up to ~20 s if AnkiConnect is not answering.
- Notes go into note type `Sentences`, deck `Sentenses`, russian with its asterisks as typed;
  comments are Markdown/plain text in the Sheet and converted to HTML for Anki. No tags.
- Constants in code; Google key from `GOOGLE_APPLICATION_CREDENTIALS`, default `key.json`.

**Tests:** pytest with fake Sheet and fake Anki clients, covering the next Pending row, a shifted
Row, a re-run `add`, inserted extra Rows, and Markdown → HTML. Real Sheet and Anki are checked by
hand once.
