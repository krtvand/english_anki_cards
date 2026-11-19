# 06 — Anki reachability (launch + poll) and `sync`

Status: done
Blocked by: 01

Spec: `../spec.md` ("Anki adapter"; user stories 39–41).

## What to build

- When Anki doesn't answer, launch it once (`open -a Anki` via an injectable launcher) and poll for up to ~20 s (injectable clock/sleep so tests are fast), then fail with a "couldn't reach Anki" message as JSON error and non-zero exit.
- `sync` command asks Anki to sync.

## Acceptance criteria

- [x] With a fake Anki that never answers, a command fails with the "couldn't reach Anki" message; the fake launcher was told to start Anki exactly once.
- [x] With a fake that answers after launch, the command succeeds.
- [x] `sync` calls the Anki sync.
