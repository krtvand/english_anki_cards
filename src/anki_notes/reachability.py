"""Making sure Anki is answering before a command talks to it: if it isn't, launch it once
and poll for up to about 20 seconds, then give up with a "couldn't reach Anki" error.

`run_command` wraps every Anki port in `ReachableAnki`, so each command gets this for free
the first time it calls any Anki method. Adapters only need a cheap `ping()`."""

import subprocess
import time
from typing import Any, Callable, Protocol

from anki_notes.errors import CommandError
from anki_notes.ports import AnkiPort

WAIT_SECONDS = 20.0
POLL_SECONDS = 0.5

UNREACHABLE = (
    "couldn't reach Anki: launched it and waited about 20 s, but AnkiConnect never answered. "
    "Check that Anki is running and the AnkiConnect add-on is installed."
)


class Clock(Protocol):
    def time(self) -> float: ...

    def sleep(self, seconds: float) -> None: ...


class SystemClock:
    def time(self) -> float:
        return time.monotonic()

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)


def launch_anki_app() -> None:
    """Start the Anki desktop app (macOS). Returns at once; Anki keeps starting in the background."""
    subprocess.run(["open", "-a", "Anki"], check=False)


class ReachableAnki:
    """An Anki port that, before the first real call, makes sure Anki is answering."""

    def __init__(self, anki: AnkiPort, *, launch: Callable[[], None], clock: Clock):
        self._anki = anki
        self._launch = launch
        self._clock = clock
        self._reached = False

    def __getattr__(self, name: str) -> Any:
        if name != "ping":
            self._ensure_reachable()
        return getattr(self._anki, name)

    def _ensure_reachable(self) -> None:
        if self._reached or self._anki.ping():
            self._reached = True
            return
        self._launch()
        deadline = self._clock.time() + WAIT_SECONDS
        while self._clock.time() < deadline:
            self._clock.sleep(POLL_SECONDS)
            if self._anki.ping():
                self._reached = True
                return
        raise CommandError(UNREACHABLE)
