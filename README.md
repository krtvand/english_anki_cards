# english-anki-cards

Turn sentences jotted down in the "phrases" tab of a Google Sheet into Notes in the Anki
`Sentenses` deck. The `make-anki-notes` Claude Code skill does the language work; the
`anki-notes` CLI (`uv run anki-notes --help`) does all reading and writing.

## One-time setup

1. **AnkiConnect.** In Anki: Tools → Add-ons → Get Add-ons…, code `2055492159`, then restart
   Anki. The CLI talks to it at `http://127.0.0.1:8765`; Anki must be running (the CLI starts
   it if it isn't).
2. **Share the Sheet with the service account.** Open the spreadsheet, Share, add
   `andrey-kartaev@constant-wonder-383212.iam.gserviceaccount.com` as **Editor**.
3. **Google key.** Copy the service account's `key.json` (from the Greek project) to the root
   of this repo. It is gitignored. To keep it elsewhere, set
   `GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json`.
4. `uv sync`, then check with `uv run anki-notes next`.

Tests (`uv run pytest`) use in-memory fakes and never touch the real Sheet or Anki.
