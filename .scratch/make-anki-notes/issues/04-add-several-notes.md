# 04 — `add` several Notes from one Row

Status: ready-for-agent
Blocked by: 03

Spec: `../spec.md` ("CLI commands: add"; user stories 19, 20).

## What to build

`add` accepts more than one Note. All Notes go to Anki (each with the same exact-russian idempotency check). The first Note is written back to the source Row and marked `1`; each extra Note becomes a new Row inserted directly below the source Row (in order), filled in and marked `1`.

## Acceptance criteria

- [ ] `add` with two Notes → two Notes in the deck; source Row updated and marked `1`; a new Row directly below with the second Note, marked `1`.
- [ ] Re-running after a Sheet failure does not duplicate Notes.
