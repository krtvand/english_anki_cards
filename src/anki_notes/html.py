"""Turning Sheet text into the HTML Anki stores. english and russian are only escaped;
the comment is escaped, then its light Markdown is converted."""

import html
import re


def escape_text(text: str) -> str:
    """HTML-escape `&`, `<`, `>` so they render as text. Nothing else changes."""
    return html.escape(text, quote=False)


def comment_to_html(text: str) -> str:
    """The comment as Anki HTML: escaped first, then `**bold**`, `*italic*`/`_italic_`,
    `-`/`*`/`•` bullet lines as a list, `#` lines as headings, other line breaks as `<br>`.
    Lists and headings are blocks, so no `<br>` is added next to them."""
    out: list[str] = []
    text_run: list[str] = []  # consecutive plain lines, joined by <br>
    items: list[str] = []  # consecutive bullet lines

    def flush() -> None:
        if text_run:
            out.append("<br>".join(text_run))
            text_run.clear()
        if items:
            out.append("<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>")
            items.clear()

    for line in escape_text(text).replace("\r\n", "\n").split("\n"):
        if bullet := _BULLET.match(line):
            if text_run:
                flush()
            items.append(_inline(bullet.group(1)))
        elif heading := _HEADING.match(line):
            flush()
            level = len(heading.group(1))
            out.append(f"<h{level}>{_inline(heading.group(2))}</h{level}>")
        else:
            if items:
                flush()
            text_run.append(_inline(line))
    flush()
    return "".join(out)


_BULLET = re.compile(r"\s*[-*•]\s+(.*)")
_HEADING = re.compile(r"\s*(#{1,6})\s+(.*)")


_BOLD = re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*")
_STAR_ITALIC = re.compile(r"(?<!\*)\*(?=[^\s*])(.+?)(?<=[^\s*])\*(?!\*)")
_UNDERSCORE_ITALIC = re.compile(r"(?<!\w)_(?=\S)(.+?)(?<=\S)_(?!\w)")


def _inline(text: str) -> str:
    text = _BOLD.sub(r"<b>\1</b>", text)
    text = _STAR_ITALIC.sub(r"<i>\1</i>", text)
    return _UNDERSCORE_ITALIC.sub(r"<i>\1</i>", text)
