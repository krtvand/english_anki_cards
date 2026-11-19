"""The one error type the CLI turns into {"error": message} with no traceback."""


class CommandError(Exception):
    """A command refused or failed for a reason the user can act on; the message says why."""
