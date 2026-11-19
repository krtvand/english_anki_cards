# 08 — The `make-anki-notes` Claude Code skill

Status: done
Blocked by: 03, 04, 05

Spec: `../spec.md` ("Solution", "Split of responsibilities", "Skill flow (one session)", user stories 1–30, 42–43); vocabulary `GLOSSARY.md`.

## What to build

`.claude/skills/make-anki-notes/SKILL.md`: the session loop that calls the CLI and does all language work (natural American-leaning english or explicit "already right", Alternatives and British notes in a Russian-language comment, keep all facts from existing comment and drop chatbot filler, russian typo fixes, never add Target phrase marks, questions → plain sentence, optional split into several Notes, duplicate judgement with discard/add anyway/Merge, mark only changed fields, approve/edit/skip/discard, sync at end). Use the `writing-for-agents` skill. Use the exact CLI command names/flags as implemented on the integration branch.

## Acceptance criteria

- [ ] SKILL.md documents the flow and every CLI invocation accurately against the implemented CLI.
