"""Turning plain text into the HTML Anki fields hold.

Placeholder from ticket 05; ticket 03 owns this module and replaces it with the full
Markdown-aware conversion."""

import html


def escape_text(text: str) -> str:
    """Plain text as HTML: special characters escaped, line breaks as <br>."""
    return html.escape(text.strip(), quote=False).replace("\n", "<br>")


def comment_to_html(text: str) -> str:
    """A comment as HTML for the Note's comment field."""
    return escape_text(text)
