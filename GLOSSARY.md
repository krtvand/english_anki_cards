# English Anki cards

Turning sentences jotted down in a Google Sheet into Anki flash cards for learning English from Russian.

## Language

### The inbox

**Sheet**:
The "phrases" tab of the Google spreadsheet, where sentences are jotted down from any device before they become notes. It is an inbox, not the source of truth.
_Avoid_: Spreadsheet, table, Google Sheets (as a whole: the spreadsheet has other tabs)

**Row**:
One entry in the Sheet: an english sentence, a russian sentence and a comment, any of which may be missing or rough.
_Avoid_: Line, entry, record

**Pending row**:
A Row whose `anki` cell is empty and which has at least an english or a russian sentence.
_Avoid_: New row, unprocessed row, todo

**Added**:
A Row marked `1`: its Notes are in Anki (new, or merged into an existing Note), and Anki owns them from then on.
_Avoid_: Done, processed, imported

**Discarded**:
A Row marked `-`: deliberately not turned into a Note, never offered again.
_Avoid_: Deleted, skipped, ignored

**Skipped**:
A Pending row passed over in one session; it stays pending and is offered again next time.
_Avoid_: Deferred, postponed

### The card

**Note**:
One note in the `Sentenses` deck, with an english sentence, a russian sentence and a comment. Russian is the front, English and the comment are the back. A Row yields one or more Notes.
_Avoid_: Card (Anki makes the card from the note), flashcard

**Target phrase**:
The part of the russian sentence marked with `*asterisks*`, the part whose translation is being learned. A russian sentence with no marks makes the whole sentence the Target phrase.
_Avoid_: Highlight, marked part, key phrase

**Alternative**:
Another natural English rendering of the Target phrase, kept in the comment alongside the main english sentence.
_Avoid_: Variant, synonym, option

**Merge**:
Folding a Row into a Note already in Anki, by updating that Note's english or comment instead of adding a new one.
_Avoid_: Update, combine

**Proposal**:
The english, russian and comment that Claude suggests for a Row, shown for approval before anything is written.
_Avoid_: Suggestion, draft, preview
