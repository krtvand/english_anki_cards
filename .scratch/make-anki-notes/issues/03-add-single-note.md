# 03 — `add` one Note: comment→HTML, write-back, safe re-run

Status: done
Blocked by: 02

Spec: `../spec.md` ("CLI commands: add", "Order of writes and safe re-runs", "Comment conversion"; user stories 31–35, 38).

## What to build

- `add` with a Row reference and one Note (english, russian, comment).
- Anki first: if a Note with exactly the same russian already exists in the deck, don't add it again; otherwise add it to deck `Sentenses`, note type `Sentences`, no tags.
- Comment converted to HTML on the way to Anki (HTML-escape first; line breaks → `<br>`, `**bold**`, `*italic*`/`_italic_`, `-`/`*`/`•` bullet lines → list, `#` headings → heading). russian and english are escaped but not Markdown-converted: russian `*asterisks*` stay literal.
- Sheet second: write the approved english/russian/comment (plain text, as given) back to the located Row and mark it `1`.

## Acceptance criteria

- [x] Note lands in the fake deck with converted comment; Row updated and marked `1`.
- [x] Comment conversion checked through `add`: line breaks, bold, italic, lists, headings, HTML escaping, russian asterisks literal.
- [x] Sheet write fails after the Anki write → a second `add` finishes the Sheet step and the deck has exactly one such Note.
- [x] Shifted/ambiguous Row behaviour from 02 holds for `add` (ambiguous → nothing written to the Sheet).
