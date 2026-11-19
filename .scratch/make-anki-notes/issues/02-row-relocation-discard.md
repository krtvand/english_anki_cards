# 02 — Finding the Row again + `discard`

Status: ready-for-agent
Blocked by: 01

Spec: `../spec.md` ("Row reference and finding the Row again", user stories 25, 36, 37).

## What to build

The Row-reference logic shared by every write command, exercised first through `discard`.

- Write commands receive the Row number and the original english and russian as `next` printed them.
- Re-read that Row number; if english/russian still match, write there. Otherwise search the tab for Rows with exactly that english and russian: one match → write there; zero or several → refuse with a clear JSON error and change nothing.
- `discard` marks the located Row `-`.

## Acceptance criteria

- [ ] `discard` marks `-`; deck unchanged.
- [ ] A Row inserted above between `next` and `discard` → the correct (shifted) Row is marked.
- [ ] Two Rows with the same content after a shift → refused, Sheet unchanged.
- [ ] Row gone entirely → refused, Sheet unchanged.
