#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Input and output shared by this skill's scripts.

Text is read and written as UTF-8 whatever the locale, a byte-order mark is
dropped, and anything that cannot be read or written exits 2 with the reason
on stderr: exit 1 is reserved for a gate that ran and failed.
"""

import sys
from pathlib import Path

BAD_INPUT = 2


def fail(message: str):
    """Exit 2 with the reason on stderr."""
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(BAD_INPUT)


def literal_newlines(value: str) -> str:
    """A --text argument writes a newline as the two characters backslash-n."""
    return value.replace("\\n", "\n")


def read_file(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        fail(f"cannot read {path}: {exc}")


def read_stdin() -> str:
    try:
        return sys.stdin.buffer.read().decode("utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        fail(f"cannot read stdin as UTF-8: {exc}")


def read_text_input(args, parser) -> str:
    """The text named by --text, --stdin or the file argument, in that order.

    An empty --text is still text (the caller reports on it). With none of the
    three, print the help and exit 2.
    """
    if args.text is not None:
        return literal_newlines(args.text).lstrip("﻿")
    if args.stdin:
        return read_stdin()
    if args.file:
        return read_file(args.file)
    parser.print_help()
    sys.exit(BAD_INPUT)


def write_output(text: str, path: str | None = None):
    """Print the result, or write it to path; an unwritable path exits 2."""
    if path:
        try:
            Path(path).write_text(text, encoding="utf-8")
        except OSError as exc:
            fail(f"cannot write {path}: {exc}")
        return
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(text)
