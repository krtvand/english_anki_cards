# Write to Anki through AnkiConnect, not by opening the collection

The Greek interview project opens `collection.anki2` directly with the `anki` library, which forces Anki to be quit, a backup before every import, a pinned note type id, mod-timestamp bookkeeping and its own AnkiWeb sync code. Here we only ever add notes to the existing `Sentences` note type (or update one), so none of those hazards apply, and we talk to the running app through the AnkiConnect add-on instead: Anki must be open (the CLI starts it if not), and phone sync is Anki's own sync, triggered once per session.
